import argparse
import time
import os
import random
from datetime import datetime

import requests

import psycopg2
import psycopg2.extensions

from pyinfraboxutils import get_logger, get_env
from pyinfraboxutils.db import connect_db
from pyinfraboxutils.token import encode_job_token

class Scheduler(object):
    def __init__(self, conn, args):
        self.conn = conn
        self.args = args
        self.namespace = get_env("INFRABOX_GENERAL_WORKER_NAMESPACE")
        self.logger = get_logger("scheduler")

    def kube_delete_job(self, job_id):
        h = {'Authorization': 'Bearer %s' % self.args.token}
        requests.delete(self.args.api_server +
                        '/apis/core.infrabox.net/v1alpha1/namespaces/%s/ibpipelineinvocations/%s' % (self.namespace, job_id,),
                        headers=h, timeout=5)

    def kube_job(self, job_id, cpu, mem, services=None):
        h = {'Authorization': 'Bearer %s' % self.args.token}

        job_token = encode_job_token(job_id).decode()

        env = [{
            'name': 'INFRABOX_JOB_ID',
            'value': job_id
        }, {
            'name': 'INFRABOX_JOB_TOKEN',
            'value': job_token
        }, {
            'name': 'INFRABOX_JOB_RESOURCES_LIMITS_MEMORY',
            'value': str(mem)
        }, {
            'name': 'INFRABOX_JOB_RESOURCES_LIMITS_CPU',
            'value': str(cpu)
        }]

        root_url = os.environ['INFRABOX_ROOT_URL']

        if services:
            for s in services:
                if 'annotations' not in s['metadata']:
                    s['metadata']['annotations'] = {}

                s['metadata']['annotations']['infrabox.net/job-id'] = job_id
                s['metadata']['annotations']['infrabox.net/job-token'] = job_token
                s['metadata']['annotations']['infrabox.net/root-url'] = root_url

        job = {
            'apiVersion': 'core.infrabox.net/v1alpha1',
            'kind': 'IBPipelineInvocation',
            'metadata': {
                'name': job_id
            },
            'spec': {
                'pipelineName': 'infrabox-default-pipeline',
                'services': services,
                'steps': {
                    'run': {
                        'resources': {
                            'limits': {
                                'memory': '%sMi' % mem,
                                'cpu': cpu
                            }
                        },
                        'env': env,
                    }
                }
            }
        }

        r = requests.post(self.args.api_server + '/apis/core.infrabox.net/v1alpha1/namespaces/%s/ibpipelineinvocations' % self.namespace,
                          headers=h, json=job, timeout=10)

        if r.status_code != 201:
            self.logger.warn(r.text)
            return False

        return True

    def schedule_job(self, job_id, cpu, memory):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT j.type, build_id, resources, definition FROM job j WHERE j.id = %s
        ''', (job_id,))
        j = cursor.fetchone()
        cursor.close()

        definition = j[3]

        cpu -= 0.2
        self.logger.info("Scheduling job to kubernetes")

        services = None

        if definition and 'services' in definition:
            services = definition['services']

        if not self.kube_job(job_id, cpu, memory, services=services):
            return

        cursor = self.conn.cursor()
        cursor.execute("UPDATE job SET state = 'scheduled' WHERE id = %s", [job_id])
        cursor.close()

        self.logger.info("Finished scheduling job")
        self.logger.info("")

    def schedule(self):
        # find jobs
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT j.id, j.cpu, j.type, j.memory, j.dependencies
            FROM job j
            WHERE j.state = 'queued' and cluster_name = %s
            ORDER BY j.created_at
        ''', [os.environ['INFRABOX_CLUSTER_NAME']])
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

            self.logger.info("")
            self.logger.info("Starting to schedule job: %s", job_id)
            self.logger.info("Dependencies: %s", dependencies)

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

            self.logger.info("Parent states: %s", result)

            # check if there's still some parent running
            parents_running = False
            for r in result:
                parent_state = r[1]
                if parent_state in ('running', 'scheduled', 'queued'):
                    # dependencies not ready
                    parents_running = True
                    break

            if parents_running:
                self.logger.info("A parent is still running, not scheduling job")
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

                self.logger.info("Checking parent %s with state %s", parent_id, parent_state)
                self.logger.info("Condition is %s", on)

                if parent_state not in on:
                    self.logger.info("Condition is not met, skipping job")
                    skipped = True
                    # dependency error, don't run this job_id
                    cursor = self.conn.cursor()
                    cursor.execute(
                        "UPDATE job SET state = 'skipped' WHERE id = (%s)", (job_id,))
                    cursor.close()
                    break

            if skipped:
                continue

            # If it's a wait job we are done here
            if job_type == "wait":
                self.logger.info("Wait job, we are done")
                cursor = self.conn.cursor()
                cursor.execute('''
                    UPDATE job SET state = 'finished', start_date = now(), end_date = now() WHERE id = %s;
                ''', (job_id,))
                cursor.close()
                continue

            self.schedule_job(job_id, cpu, memory)

    def handle_aborts(self):
        cluster_name = os.environ['INFRABOX_CLUSTER_NAME']

        cursor = self.conn.cursor()
        cursor.execute('''
            WITH all_aborts AS (
                DELETE FROM "abort" RETURNING job_id
            ), jobs_to_abort AS (
                SELECT j.id, j.state FROM all_aborts
                JOIN job j
                    ON all_aborts.job_id = j.id
                    AND j.state not in ('finished', 'failure', 'error', 'killed')
                    AND cluster_name = %s
            ), jobs_not_started_yet AS (
                UPDATE job SET state = 'killed'
                WHERE id in (SELECT id FROM jobs_to_abort WHERE state in ('queued'))
            )

            SELECT id FROM jobs_to_abort WHERE state in ('scheduled', 'running', 'queued')
        ''', [cluster_name])

        aborts = cursor.fetchall()
        cursor.close()

        for abort in aborts:
            job_id = abort[0]
            self.kube_delete_job(job_id)

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

    def handle_timeouts(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT j.id FROM job j
            WHERE j.start_date < (NOW() - (j.timeout * INTERVAL '1' SECOND))
            AND j.state = 'running'
        ''')
        aborts = cursor.fetchall()
        cursor.close()

        for abort in aborts:
            job_id = abort[0]
            self.kube_delete_job(job_id)

            cursor = self.conn.cursor()
            cursor.execute("SELECT output FROM console WHERE job_id = %s ORDER BY date", (job_id,))
            lines = cursor.fetchall()

            output = ""
            for line in lines:
                output += line[0]

            output += "Aborted due to timeout"

            # Update state
            cursor.execute("""
                UPDATE job SET state = 'error', console = %s, end_date = current_timestamp, message = 'Aborted due to timeout'
                WHERE id = %s""", (output, job_id,))

            cursor.close()

    def handle_orphaned_jobs(self):
        self.logger.debug("Handling orphaned jobs")

        h = {'Authorization': 'Bearer %s' % self.args.token}
        r = requests.get(self.args.api_server + '/apis/core.infrabox.net/v1alpha1/namespaces/%s/ibpipelineinvocations' % self.namespace,
                         headers=h,
                         timeout=10)
        data = r.json()

        if 'items' not in data:
            return

        for j in data['items']:
            if 'metadata' not in j:
                continue

            metadata = j['metadata']
            name = metadata['name']
            job_id = name

            cursor = self.conn.cursor()
            cursor.execute('''SELECT state FROM job where id = %s''', (job_id,))
            result = cursor.fetchall()
            cursor.close()

            if not result:
                self.logger.info('Deleting orphaned job %s', job_id)
                self.kube_delete_job(job_id)
                continue

            last_state = result[0][0]
            if last_state in ('killed', 'finished', 'error', 'finished'):
                self.kube_delete_job(job_id)
                continue

            start_date = None
            end_date = None
            delete_job = False
            current_state = 'scheduled'
            message = None

            if j.get('status', None):
                status = j['status']
                s = status.get('state', "preparing")
                message = status.get('message', None)

                if s in ["preparing", "scheduling"]:
                    current_state = 'scheduled'

                if s in ["running", "finalizing"]:
                    current_state = 'running'

                if s == "terminated":
                    current_state = 'error'

                    if 'stepStatuses' in status and status['stepStatuses']:
                        stepStatus = status['stepStatuses'][-1]
                        exit_code = stepStatus['State']['terminated']['exitCode']

                        if exit_code == 0:
                            current_state = 'finished'
                        else:
                            current_state = 'failure'
                            message = stepStatus['State']['terminated'].get('message', "")

                    delete_job = True

                if s == "error":
                    current_state = 'error'
                    delete_job = True
                    start_date = datetime.now()
                    end_date = datetime.now()

                start_date = status.get('startTime', None)
                end_date = status.get('completionTime', None)

            if last_state == current_state:
                continue

            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE job SET state = %s, start_date = %s, end_date = %s, message = %s
                WHERE id = %s
            """, (current_state, start_date, end_date, message, job_id))
            cursor.close()

            if delete_job:
                # collect console output
                cursor = self.conn.cursor()
                cursor.execute("""
                    SELECT output FROM console WHERE job_id = %s
                    ORDER BY date
                """, [job_id])
                lines = cursor.fetchall()
                cursor.close()

                output = ""
                for l in lines:
                    output += l[0]

                cursor = self.conn.cursor()
                cursor.execute("""
                    UPDATE job SET console = %s WHERE id = %s;
                    DELETE FROM console WHERE job_id = %s;
                """, [output, job_id, job_id])
                cursor.close()

                self.logger.info('Deleting job %s', job_id)
                self.kube_delete_job(job_id)

    def get_default_cluster(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name, labels
            FROM cluster
            WHERE active = true
        """)
        result = cursor.fetchall()
        cursor.close()

        random.shuffle(result)

        for row in result:
            cluster_name = row[0]
            labels = row[1]

            for l in labels:
                if l == 'default':
                    return cluster_name

        return None

    def assign_cluster(self):
        cluster_name = self.get_default_cluster()

        if not cluster_name:
            self.logger.warn("No default cluster found, jobs will not be started")
            return

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id
            FROM job
            WHERE cluster_name is null
        """)
        jobs = cursor.fetchall()
        cursor.close()

        for j in jobs:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE job
                SET cluster_name = %s
                WHERE id = %s
            """, [cluster_name, j[0]])
            cursor.close()

    def update_cluster_state(self):
        cluster_name = os.environ['INFRABOX_CLUSTER_NAME']
        labels = []

        if os.environ['INFRABOX_CLUSTER_LABELS']:
            labels = os.environ['INFRABOX_CLUSTER_LABELS'].split(',')

        root_url = os.environ['INFRABOX_ROOT_URL']

        h = {'Authorization': 'Bearer %s' % self.args.token}
        r = requests.get(self.args.api_server + '/api/v1/nodes',
                         headers=h,
                         timeout=10)
        data = r.json()

        memory = 0
        cpu = 0
        nodes = 0

        items = data.get('items', [])

        for i in items:
            nodes += 1
            cpu += int(i['status']['capacity']['cpu'])
            mem = i['status']['capacity']['memory']
            mem = mem.replace('Ki', '')
            memory += int(mem)

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO cluster (name, labels, root_url, nodes, cpu_capacity, memory_capacity, active)
            VALUES(%s, %s, %s, %s, %s, %s, true)
            ON CONFLICT (name) DO UPDATE
            SET labels = %s, root_url = %s, nodes = %s, cpu_capacity = %s, memory_capacity = %s
            WHERE cluster.name = %s """, [cluster_name, labels, root_url, nodes, cpu, memory, labels,
                                          root_url, nodes, cpu, memory, cluster_name])
        cursor.close()

    def _inactive(self):
        cluster_name = os.environ['INFRABOX_CLUSTER_NAME']
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT active
            FROM cluster
            WHERE name = %s """, [cluster_name])
        active = cursor.fetchone()[0]
        cursor.close()

        return not active

    def handle(self):
        self.update_cluster_state()

        try:
            self.handle_timeouts()
            self.handle_aborts()
            self.handle_orphaned_jobs()
        except Exception as e:
            self.logger.exception(e)

        cluster_name = os.environ['INFRABOX_CLUSTER_NAME']
        if cluster_name == 'master':
            self.assign_cluster()

        if self._inactive():
            self.logger.info('Cluster set to inactive, sleeping...')
            time.sleep(5)
            return

        self.schedule()

    def run(self):
        self.logger.info("Starting scheduler")

        while True:
            self.handle()
            time.sleep(2)

def main():
    # Arguments
    parser = argparse.ArgumentParser(prog="scheduler.py")
    args = parser.parse_args()

    get_env('INFRABOX_VERSION')
    get_env('INFRABOX_CLUSTER_NAME')
    get_env('INFRABOX_DATABASE_DB')
    get_env('INFRABOX_DATABASE_USER')
    get_env('INFRABOX_DATABASE_PASSWORD')
    get_env('INFRABOX_DATABASE_HOST')
    get_env('INFRABOX_DATABASE_PORT')
    get_env('INFRABOX_ROOT_URL')
    get_env('INFRABOX_GENERAL_DONT_CHECK_CERTIFICATES')
    get_env('INFRABOX_GENERAL_WORKER_NAMESPACE')

    # try to read from filesystem
    with open('/var/run/secrets/kubernetes.io/serviceaccount/token', 'r') as f:
        args.token = str(f.read()).strip()

    args.api_server = "https://" + get_env('INFRABOX_KUBERNETES_MASTER_HOST') \
                                 + ":" + get_env('INFRABOX_KUBERNETES_MASTER_PORT')

    os.environ['REQUESTS_CA_BUNDLE'] = '/var/run/secrets/kubernetes.io/serviceaccount/ca.crt'

    conn = connect_db()
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    scheduler = Scheduler(conn, args)
    scheduler.run()

if __name__ == "__main__":
    main()
