import logging
import argparse
import time
import os
import requests
import psycopg2
import psycopg2.extensions

from pyinfraboxutils import get_logger, get_env, print_stackdriver
from pyinfraboxutils.db import connect_db

def gerrit_enabled():
    return os.environ['INFRABOX_GERRIT_ENABLED'] == 'true'

def use_host_docker_daemon():
    return os.environ['INFRABOX_JOB_USE_HOST_DOCKER_DAEMON'] == 'true'

class Scheduler(object):
    def __init__(self, conn, args):
        self.conn = conn
        self.args = args
        self.namespace = get_env("INFRABOX_GENERAL_WORKER_NAMESPACE")
        self.logger = get_logger("scheduler")

        if self.args.loglevel == 'debug':
            self.logger.setLevel(logging.DEBUG)
        elif self.args.loglevel == 'info':
            self.logger.setLevel(logging.INFO)
        else:
            self.logger.setLevel(logging.INFO)


    def kube_delete_namespace(self, job_id):
        h = {'Authorization': 'Bearer %s' % self.args.token}
        namespace_name = "ib-%s" % job_id

        # delete the namespace
        p = {"gracePeriodSeconds": 0}
        requests.delete(self.args.api_server + '/api/v1/namespaces/%s' % (namespace_name,),
                        headers=h, params=p, timeout=10)


    def kube_delete_job(self, job_id):
        h = {'Authorization': 'Bearer %s' % self.args.token}
        p = {"gracePeriodSeconds": 0}
        requests.delete(self.args.api_server +
                        '/apis/infrabox.net/v1alpha1/namespaces/%s/jobs/%s' % (self.namespace, job_id,),
                        headers=h, params=p, timeout=5)

    def kube_job(self, job_id, cpu, mem, additional_env=None):
        h = {'Authorization': 'Bearer %s' % self.args.token}

        job = {
            'apiVersion': 'infrabox.net/v1alpha1',
            'kind': 'Job',
            'metadata': {
                'name': job_id
            },
            'spec': {
                'resources': {
                    'limits': {
                        'memory': '%sMi' % mem,
                        'cpu': cpu
                    }
                },
                'env': additional_env
            }
        }

        r = requests.post(self.args.api_server + '/apis/infrabox.net/v1alpha1/namespaces/%s/jobs' % self.namespace,
                          headers=h, json=job, timeout=10)

        if r.status_code != 201:
            self.logger.info('API Server response')
            self.logger.info(r.text)
            return False

        return True

    def create_kube_namespace(self, job_id, _k8s_resources):
        self.logger.info("Provisioning kubernetes namespace")
        h = {'Authorization': 'Bearer %s' % self.args.token}

        namespace_name = "ib-%s" % job_id
        ns = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": namespace_name,
                "labels": {
                    "infrabox-resource": "kubernetes",
                    "infrabox-job-id": job_id,
                }
            }
        }

        r = requests.post(self.args.api_server + '/api/v1/namespaces',
                          headers=h, json=ns, timeout=10)

        if r.status_code != 201:
            self.logger.warn("Failed to create Namespace: %s", r.text)
            return False

#        rq = {
#            "apiVersion": "v1",
#            "kind": "ResourceQuota",
#            "metadata": {
#                "name": "compute-resources",
#                "namespace": namespace_name
#            },
#            "spec": {
#                "hard": {
#                    "limits.cpu": k8s_resources['limits']['cpu'],
#                    "limits.memory": k8s_resources['limits']['memory']
#                }
#            }
#        }
#
#        #r = requests.post(self.args.api_server + '/api/v1/namespaces/' + namespace_name + '/resourcequotas',
#        #                  headers=h, json=rq, timeout=10)
#
#        if r.status_code != 201:
#            self.logger.warn("Failed to create ResourceQuota: %s" % r.text)
#            return False

        role = {
            'kind': 'Role',
            'apiVersion': 'rbac.authorization.k8s.io/v1beta1',
            'metadata': {
                'name': 'infrabox',
                'namespace': namespace_name
            },
            'rules': [{
                'apiGroups': ['', 'extensions', 'apps', 'batch'],
                'resources': ['*'],
                'verbs': ['*']
            }, {
                'apiGroups': ['rbac.authorization.k8s.io'],
                'resources': ['roles', 'rolebindings'],
                'verbs': ['*']
            }, {
                'apiGroups': ['policy'],
                'resources': ['poddisruptionbudgets'],
                'verbs': ['*']
            }]
        }

        r = requests.post(self.args.api_server +
                          '/apis/rbac.authorization.k8s.io/v1beta1/namespaces/%s/roles' % namespace_name,
                          headers=h, json=role, timeout=10)

        if r.status_code != 201:
            self.logger.warn("Failed to create Role: %s", r.text)
            return False

        rb = {
            "kind": "RoleBinding",
            "apiVersion": "rbac.authorization.k8s.io/v1beta1",
            "metadata": {
                "name": namespace_name
            },
            "subjects": [{
                "kind": "ServiceAccount",
                "name": "default",
                "namespace": namespace_name
            }],
            "roleRef": {
                "kind": "Role",
                "name": "infrabox",
                "apiGroup": "rbac.authorization.k8s.io"
            }
        }

        r = requests.post(self.args.api_server +
                          '/apis/rbac.authorization.k8s.io/v1beta1/namespaces/%s/rolebindings' % namespace_name,
                          headers=h, json=rb, timeout=10)

        if r.status_code != 201:
            self.logger.warn("Failed to create RoleBinding: %s", r.text)
            return False

        rb = {
            "kind": "RoleBinding",
            "apiVersion": "rbac.authorization.k8s.io/v1beta1",
            "metadata": {
                "name": namespace_name + '-discovery'
            },
            "subjects": [{
                "kind": "ServiceAccount",
                "name": "default",
                "namespace": namespace_name
            }],
            "roleRef": {
                "kind": "ClusterRole",
                "name": "system:discover",
                "apiGroup": "rbac.authorization.k8s.io"
            }
        }

        r = requests.post(self.args.api_server +
                          '/apis/rbac.authorization.k8s.io/v1beta1/namespaces/%s/rolebindings' % namespace_name,
                          headers=h, json=rb, timeout=10)

        if r.status_code != 201:
            self.logger.warn("Failed to create RoleBinding for discovery: %s", r.text)
            return False

        # find secret
        r = requests.get(self.args.api_server + '/api/v1/namespaces/%s/secrets' % namespace_name,
                         headers=h, timeout=5)

        if r.status_code != 200:
            self.logger.warn("Failed to get service account secret: %s", r.txt)
            return False

        data = r.json()
        secret = data['items'][0]

        env = [
            {"name": "INFRABOX_RESOURCES_KUBERNETES_CA_CRT", "value": secret['data']['ca.crt']},
            {"name": "INFRABOX_RESOURCES_KUBERNETES_TOKEN", "value":  secret['data']['token']},
            {"name": "INFRABOX_RESOURCES_KUBERNETES_NAMESPACE", "value": secret['data']['namespace']},
            {"name": "INFRABOX_RESOURCES_KUBERNETES_MASTER_URL", "value": self.args.api_server}
        ]

        return env

    def schedule_job(self, job_id, cpu, memory):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT j.type, build_id, resources FROM job j WHERE j.id = %s
        ''', (job_id,))
        j = cursor.fetchone()
        cursor.close()

        build_id = j[1]
        resources = j[2]

        cpu -= 0.2

        additional_env = None
        if resources and resources.get('kubernetes', None):
            k8s = resources.get('kubernetes', None)
            additional_env = self.create_kube_namespace(job_id, k8s)

            if not additional_env:
                self.logger.warn('Failed to create kubernetes namespace')
                cursor = self.conn.cursor()
                cursor.execute('''
                    UPDATE job
                    SET state = 'error', console = 'Failed to create kubernetes namespace'
                    WHERE id = %s''', [job_id])
                cursor.close()
                return

        self.logger.info("Scheduling job to kubernetes")

        if not self.kube_job(job_id, cpu, memory, additional_env=additional_env):
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
                UPDATE job SET state = 'error', console = %s, end_date = current_timestamp
                WHERE id = %s""", (output, job_id,))

            cursor.close()

    def handle_orphaned_namespaces(self):
        h = {'Authorization': 'Bearer %s' % self.args.token}
        r = requests.get(self.args.api_server + '/api/v1/namespaces', headers=h, timeout=10)
        data = r.json()

        if 'items' not in data:
            self.logger.warn('No data returned')
            return

        for j in data['items']:
            metadata = j.get('metadata', None)
            if not metadata:
                continue

            labels = metadata.get('labels', None)
            if not labels:
                continue

            for key in labels:
                if key != 'infrabox-job-id':
                    continue

                job_id = labels[key]

                cursor = self.conn.cursor()
                cursor.execute('''SELECT state FROM job where id = %s''', (job_id,))
                result = cursor.fetchall()
                cursor.close()

                if len(result) != 1:
                    continue

                state = result[0][0]

                if state in ('queued', 'scheduled', 'running'):
                    continue

                self.logger.info('Deleting orphaned namespace ib-%s', job_id)
                self.kube_delete_namespace(job_id)

    def handle_orphaned_jobs(self):
        h = {'Authorization': 'Bearer %s' % self.args.token}
        r = requests.get(self.args.api_server + '/apis/infrabox.net/v1alpha1/namespaces/%s/jobs' % self.namespace,
                         headers=h,
                         timeout=10)
        data = r.json()

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

            if len(result) != 1:
                continue

            state = result[0][0]

            if state in ('queued', 'scheduled', 'running'):
                continue

            self.logger.info('Deleting orphaned job %s', job_id)
            self.kube_delete_job(job_id)

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
            self.handle_orphaned_namespaces()
        except Exception as e:
            self.logger.exception(e)

        if self._inactive():
            self.logger.info('Cluster set to inactive, sleeping...')
            time.sleep(5)
            return

        self.schedule()

    def run(self):
        while True:
            self.handle()
            time.sleep(2)

def main():
    # Arguments
    parser = argparse.ArgumentParser(prog="scheduler.py")
    parser.add_argument("--docker-registry", required=True, type=str,
                        help="Host for the registry to use")
    parser.add_argument("--loglevel", choices=['debug', 'info', 'warning'],
                        help="Log level")
    parser.add_argument("--tag", required=True, type=str,
                        help="Image tag to use for internal images")

    args = parser.parse_args()

    get_env('INFRABOX_SERVICE')
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
    get_env('INFRABOX_JOB_MAX_OUTPUT_SIZE')
    get_env('INFRABOX_JOB_MOUNT_DOCKER_SOCKET')
    get_env('INFRABOX_JOB_SECURITY_CONTEXT_CAPABILITIES_ENABLED')

    if get_env('INFRABOX_GERRIT_ENABLED') == 'true':
        get_env('INFRABOX_GERRIT_USERNAME')
        get_env('INFRABOX_GERRIT_HOSTNAME')
        get_env('INFRABOX_GERRIT_PORT')

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
    try:
        main()
    except:
        print_stackdriver()
