import logging
import time
import os
import subprocess
import yaml
import psycopg2
import psycopg2.extensions

logging.basicConfig(
    format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%d-%m-%Y:%H:%M:%S',
    level=logging.WARN
)

logger = logging.getLogger("scheduler")

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

class Scheduler(object):
    def __init__(self, conn):
        self.conn = conn

    def kube_job(self, job_id, build_id, cpu, memory, job_type):
        compose = {
            "version": "2",
            "services": {
                "job-%s" % job_id: {
                    "image": os.environ['INFRABOX_DOCKER_REGISTRY'] + '/infrabox/job',
                    "network_mode": "host",
                    "command": "/usr/local/bin/wait-for-webserver.sh localhost:5000 /usr/local/bin/entrypoint.sh --type %s" % job_type,
                    "volumes": [
                        "/var/run/docker.sock:/var/run/docker.sock"
                    ],
                    "environment": [
                        "INFRABOX_JOB_ID=%s" % job_id,
                        "INFRABOX_GENERAL_NO_CHECK_CERTIFICATES=true",
                        "INFRABOX_JOB_API_URL=http://localhost:5000",
                        "INFRABOX_SERVICE=job",
                        "INFRABOX_VERSION=latest",
                        "INFRABOX_DOCKER_REGISTRY_URL=localhost:30202",
                        "INFRABOX_CLAIR_ENABLED=false",
                        "INFRABOX_LOCAL_CACHE_ENABLED=false",
                        "INFRABOX_JOB_MAX_OUTPUT_SIZE=%s" % os.environ['INFRABOX_JOB_MAX_OUTPUT_SIZE'],
                        "INFRABOX_DOCKER_REGISTRY_ADMIN_USERNAME=admin",
                        "INFRABOX_DOCKER_REGISTRY_ADMIN_PASSWORD=admin",
                        "INFRABOX_DASHBOARD_URL=http://localhost:30201"
                    ],
                    "privileged": True,
                    "depends_on": [
                        "job-api-%s" % job_id
                    ]
                },
                "job-api-%s" % job_id: {
                    "image": os.environ['INFRABOX_DOCKER_REGISTRY'] + '/infrabox/job-api',
                    "network_mode": "host",
                    "environment": [
                        "INFRABOX_JOB_ID=%s" % job_id,
                        "INFRABOX_GENERAL_NO_CHECK_CERTIFICATES=true",
                        "INFRABOX_SERVICE=job-api",
                        "INFRABOX_VERSION=latest",
                        "INFRABOX_JOB_MAX_OUTPUT_SIZE=%s" % os.environ['INFRABOX_JOB_MAX_OUTPUT_SIZE'],
                        "INFRABOX_DASHBOARD_URL=http://localhost:30201",
                        "INFRABOX_STORAGE_GCS_ENABLED=false",
                        "INFRABOX_STORAGE_S3_ENABLED=true",
                        "INFRABOX_GERRIT_ENABLED=false",
                        "INFRABOX_STORAGE_S3_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE",
                        "INFRABOX_STORAGE_S3_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                        "INFRABOX_STORAGE_S3_PORT=9000",
                        "INFRABOX_STORAGE_S3_ENDPOINT=localhost",
                        "INFRABOX_STORAGE_S3_SECURE=false",
                        "INFRABOX_STORAGE_S3_REGION=us-east-1",
                        "INFRABOX_STORAGE_S3_CONTAINER_CONTENT_CACHE_BUCKET=infrabox-container-content-cache",
                        "INFRABOX_STORAGE_S3_PROJECT_UPLOAD_BUCKET=infrabox-project-upload",
                        "INFRABOX_STORAGE_S3_CONTAINER_OUTPUT_BUCKET=infrabox-container-output",
                        "INFRABOX_DATABASE_USER=%s" % os.environ['INFRABOX_DATABASE_USER'],
                        "INFRABOX_DATABASE_PASSWORD=%s" % os.environ['INFRABOX_DATABASE_PASSWORD'],
                        "INFRABOX_DATABASE_HOST=%s" % os.environ['INFRABOX_DATABASE_HOST'],
                        "INFRABOX_DATABASE_PORT=%s" % os.environ['INFRABOX_DATABASE_PORT'],
                        "INFRABOX_DATABASE_DB=%s" % os.environ['INFRABOX_DATABASE_DB']
                    ],
                }
            }
        }


        with open("/tmp/docker-compose.yaml", "w") as outfile:
            yaml.dump(compose, outfile, default_flow_style=False)

        execute(("docker-compose", "-f", "/tmp/docker-compose.yaml", "up", "--abort-on-container-exit"))

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

    def handle(self):
        self.schedule()

    def run(self):
        while True:
            self.handle()
            time.sleep(5)

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

    conn = psycopg2.connect(dbname=os.environ['INFRABOX_DATABASE_DB'],
                            user=os.environ['INFRABOX_DATABASE_USER'],
                            password=os.environ['INFRABOX_DATABASE_PASSWORD'],
                            host=os.environ['INFRABOX_DATABASE_HOST'],
                            port=os.environ['INFRABOX_DATABASE_PORT'])

    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    scheduler = Scheduler(conn)
    scheduler.run()

if __name__ == "__main__":
    main()
