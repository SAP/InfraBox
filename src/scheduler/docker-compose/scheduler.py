#pylint: disable=superfluous-parens
import logging
import time
import os
import sys
import subprocess
import shutil
import psycopg2
import psycopg2.extensions

from pyinfraboxutils import get_logger
from pyinfraboxutils.db import connect_db
from pyinfraboxutils.token import encode_job_token

logger = get_logger('scheduler')

def execute(command):
    logger.info(command)
    process = subprocess.Popen(command,
                               shell=False,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines=True)

    # Poll process for new output until finished
    while True:
        line = process.stdout.readline()
        if not line:
            break

        line = line.rstrip()
        print line

    process.wait()

    exitCode = process.returncode
    if exitCode != 0:
        raise Exception("")


def clear_dir(d):
    for f in os.listdir(d):
        p = os.path.join(d, f)
        try:
            if os.path.isfile(p):
                os.unlink(p)
            elif os.path.isdir(p):
                shutil.rmtree(p)
        except Exception as e:
            print(e)

class Scheduler(object):
    def __init__(self):
        self.conn = connect_db()
        self.conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        self.daemon_json = None

    def kube_job(self, job_id, _build_id, _cpu, _memory, _job_type):
        repo_dir = '/tmp/infrabox-compose/repo'
        clear_dir(repo_dir)

        token = encode_job_token(job_id)

        prefix = os.environ.get('INFRABOX_DOCKER_COMPOSE_PROJECT_PREFIX', 'compose')

        cmd = [
            'docker',
            'run',
            '--rm',
            '-e', "INFRABOX_JOB_ID=%s" % job_id,
            '-e', "INFRABOX_GENERAL_DONT_CHECK_CERTIFICATES=true",
            '-e', "INFRABOX_JOB_API_URL=http://nginx-ingress/api/job",
            '-e', "INFRABOX_SERVICE=job",
            '-e', "INFRABOX_VERSION=latest",
            '-e', "INFRABOX_DOCKER_REGISTRY_URL=localhost:8090",
            '-e', "INFRABOX_LOCAL_CACHE_ENABLED=false",
            '-e', "INFRABOX_JOB_MAX_OUTPUT_SIZE=%s" % os.environ['INFRABOX_JOB_MAX_OUTPUT_SIZE'],
            '-e', "INFRABOX_DASHBOARD_URL=http://localhost",
            '-e', "INFRABOX_JOB_MOUNT_DOCKER_SOCKET=false",
            '-e', "INFRABOX_JOB_TOKEN=%s" % token,
            '-e', "INFRABOX_JOB_DAEMON_JSON=%s" % self.daemon_json,
            '-e', "INFRABOX_JOB_REPO_MOUNT_PATH=%s" % repo_dir,
            '--privileged',
            '--network=%s_infrabox' % prefix,
            '-v', '/var/run/docker.sock:/var/run/docker.sock',
            '-v', '/tmp/infrabox-compose/repo:/tmp/infrabox-compose/repo',
            '--name=ib-job-%s' % job_id,
            '--link=%s_nginx-ingress_1:nginx-ingress' % prefix,
            os.environ['INFRABOX_DOCKER_REGISTRY'] + '/job'
        ]

        try:
            execute(cmd)
        except:
            execute(['docker', 'network', 'ls']
            pass

    def schedule_job(self, job_id, cpu, memory):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT j.type, build_id FROM job j WHERE j.id = %s
        ''', (job_id,))
        j = cursor.fetchone()
        cursor.close()

        job_type = j[0]
        build_id = j[1]

        if cpu == 1:
            cpu = cpu * 0.8
        else:
            cpu = cpu * 0.9

        logger.info("Scheduling job")

        if job_type == 'create_job_matrix':
            job_type = 'create'
        elif job_type == "run_project_container" or job_type == "run_docker_compose":
            job_type = 'run'
        else:
            logger.error("Unknown job type: %s", job_type)
            return

        cursor = self.conn.cursor()
        cursor.execute("UPDATE job SET state = 'scheduled' WHERE id = %s", [job_id])
        cursor.close()

        if not self.kube_job(job_id, build_id, cpu, memory, job_type):
            return

        logger.info("Finished scheduling job")
        logger.info("")

    def schedule(self):
        # find jobs
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT j.id, j.cpu, j.type, j.memory, j.dependencies
            FROM job j
            WHERE j.state = 'queued'
            ORDER BY j.created_at
        ''')
        jobs = cursor.fetchall()
        cursor.close()

        if not jobs:
            # No queued job
            return

        # check dependecies
        for j in jobs:
            job_id = j[0]
            cpu = j[1]
            job_type = j[2]
            memory = j[3]
            dependencies = j[4]

            logger.info("")
            logger.info("Starting to schedule job: %s", job_id)
            logger.info("Dependencies: %s", dependencies)

            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT id, state
                FROM job
                WHERE id IN (
                    SELECT (deps->>'job-id')::uuid
                    FROM job, jsonb_array_elements(job.dependencies) as deps
                    WHERE id = %s
                )
            ''', (job_id,))
            result = cursor.fetchall()
            cursor.close()

            logger.info("Parent states: %s", result)

            # check if there's still some parent running
            parents_running = False
            for r in result:
                parent_state = r[1]
                if parent_state in ('running', 'scheduled', 'queued'):
                    # dependencies not ready
                    parents_running = True
                    break

            if parents_running:
                logger.info("A parent is still running, not scheduling job")
                continue

            # check if conditions are met
            skipped = False
            for r in result:
                on = None
                parent_id = r[0]
                parent_state = r[1]
                for dep in dependencies:
                    if dep['job-id'] == parent_id:
                        on = dep['on']

                assert on

                logger.info("Checking parent %s with state %s", parent_id, parent_state)
                logger.info("Condition is %s", on)

                if parent_state not in on:
                    logger.info("Condition is not met, skipping job")
                    skipped = True
                    # dependency error, don't run this job_id
                    cursor = self.conn.cursor()
                    cursor.execute(
                        "UPDATE job SET state = 'skipped' WHERE id = (%s)", (job_id,))
                    cursor.close()
                    break

            if skipped:
                logger.info("Job is skipped")
                continue

            # If it's a wait job we are done here
            if job_type == "wait":
                logger.info("Wait job, we are done")
                cursor = self.conn.cursor()
                cursor.execute('''
                    UPDATE job SET state = 'finished', start_date = now(), end_date = now() WHERE id = %s;
                ''', (job_id,))
                cursor.close()
                logger.info("It's a wait job")
                continue

            self.schedule_job(job_id, cpu, memory)
            return

    def handle_aborts(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            WITH all_aborts AS (
                DELETE FROM "abort" RETURNING job_id
            ), jobs_to_abort AS (
                SELECT j.id, j.state FROM all_aborts
                JOIN job j
                    ON all_aborts.job_id = j.id
                    AND j.state not in ('finished', 'failure', 'error', 'killed')
            ), jobs_not_started_yet AS (
                UPDATE job SET state = 'killed'
                WHERE id in (SELECT id FROM jobs_to_abort WHERE state in ('queued'))
            )

            SELECT id FROM jobs_to_abort WHERE state in ('scheduled', 'running', 'queued')
        ''')

        aborts = cursor.fetchall()
        cursor.close()

        for abort in aborts:
            job_id = abort[0]
            try:
                execute(('docker', 'kill', job_id))
            except:
                pass

            cursor = self.conn.cursor()
            cursor.execute("SELECT output FROM console WHERE job_id = %s ORDER BY date", (job_id,))
            lines = cursor.fetchall()

            output = ""
            for line in lines:
                output += line[0]

            # Update state
            cursor.execute("""
                UPDATE job SET state = 'killed', console = %s, end_date = current_timestamp
                WHERE id = %s AND state IN ('scheduled', 'running', 'queued')""", (output, job_id,))

            cursor.close()

    def handle(self):
        self.handle_aborts()
        self.schedule()

    def run(self):
        daemon_json_path = '/etc/docker/daemon.json'
        if not os.path.exists(daemon_json_path):
            logger.error('%s does not exist', daemon_json_path)
            sys.exit(1)

        with open(daemon_json_path) as daemon_json:
            self.daemon_json = str(daemon_json.read())

        while True:
            self.handle()
            time.sleep(1)

def get_env(name):
    if name not in os.environ:
        raise Exception("%s not set" % name)
    return os.environ[name]

def main():
    logger.setLevel(logging.INFO)

    get_env('INFRABOX_SERVICE')
    get_env('INFRABOX_VERSION')
    get_env('INFRABOX_DATABASE_DB')
    get_env('INFRABOX_DATABASE_USER')
    get_env('INFRABOX_DATABASE_PASSWORD')
    get_env('INFRABOX_DATABASE_HOST')
    get_env('INFRABOX_DATABASE_PORT')
    get_env('INFRABOX_DOCKER_REGISTRY')

    scheduler = Scheduler()
    scheduler.run()

if __name__ == "__main__":
    main()
