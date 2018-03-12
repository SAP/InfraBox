import logging
import argparse
import time
import os
import sys
import psycopg2
import psycopg2.extensions
import requests
from prometheus_client import start_http_server, Histogram, Counter

from pyinfraboxutils import get_logger, get_env, print_stackdriver
from pyinfraboxutils.leader import is_leader
from pyinfraboxutils.db import connect_db
from pyinfraboxutils.token import encode_job_token


# pylint: disable=no-value-for-parameter
LOOP_SECONDS = Histogram('infrabox_scheduler_loop_seconds', 'Time spent for one scheduler loop iteration')
ORPHANED_JOBS = Counter('infrabox_scheduler_orphaned_jobs_total', 'Number of removed orphaned jobs')
ABORTED_JOBS = Counter('infrabox_scheduler_killed_jobs_total', 'Number of killed jobs')
SCHEDULED_JOBS = Counter('infrabox_scheduler_scheduled_jobs_total', 'Number of scheduled jobs')
TIMEOUT_JOBS = Counter('infrabox_scheduler_timeout_jobs_total', 'Number of timed out scheduled jobs')
ORPHANED_NAMESPACES = Counter('infrabox_scheduler_orphaned_namespaces_total', 'Number of removed orphaned namespaces')

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
        self.daemon_json = None

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

        # find pods which belong to the job
        p = {"labelSelector": "job-name=%s" % job_id}
        r = requests.get(self.args.api_server + '/api/v1/namespaces/%s/pods' % (self.namespace,),
                         headers=h, params=p, timeout=5)
        pods = r.json()

        # delete the job
        p = {"gracePeriodSeconds": 0}
        requests.delete(self.args.api_server + '/apis/batch/v1/namespaces/%s/jobs/%s' % (self.namespace, job_id,),
                        headers=h, params=p, timeout=5)

        # If there are no pods it is already set to None
        # so we check it before the loop
        if not pods.get('items', None):
            return

        # delete all pods
        for pod in pods.get('items', []):
            pod_name = pod['metadata']['name']

            p = {"gracePeriodSeconds": 0}
            requests.delete(self.args.api_server + '/api/v1/namespaces/%s/pods/%s' % (self.namespace, pod_name,),
                            headers=h, params=p, timeout=5)

    def kube_job(self, job_id, build_id, cpu, mem, job_type, additional_env=None):
        h = {'Authorization': 'Bearer %s' % self.args.token}
        volumes = [{
            "name": "data-dir",
            "emptyDir": {}
        }, {
            "name": "repo",
            "emptyDir": {}
        }]

        volume_mounts = [{
            "mountPath": "/data",
            "name": "data-dir"
        }, {
            "mountPath": "/repo",
            "name": "repo"
        }]

        env = [{
            "name": "INFRABOX_JOB_ID",
            "value": job_id
        }, {
            "name": "INFRABOX_GENERAL_DONT_CHECK_CERTIFICATES",
            "value": os.environ['INFRABOX_GENERAL_DONT_CHECK_CERTIFICATES']
        }, {
            "name": "INFRABOX_JOB_API_URL",
            "value": os.environ['INFRABOX_ROOT_URL'] + '/api/job'
        }, {
            "name": "INFRABOX_JOB_GIT_URL",
            "value": "http://localhost:8080"
        }, {
            "name": "INFRABOX_SERVICE",
            "value": "job"
        }, {
            "name": "INFRABOX_VERSION",
            "value": self.args.tag
        }, {
            "name": "INFRABOX_DOCKER_REGISTRY_URL",
            "value": os.environ['INFRABOX_DOCKER_REGISTRY_URL']
        }, {
            "name": "INFRABOX_LOCAL_CACHE_ENABLED",
            "value": os.environ['INFRABOX_LOCAL_CACHE_ENABLED']
        }, {
            "name": "INFRABOX_JOB_MAX_OUTPUT_SIZE",
            "value": os.environ['INFRABOX_JOB_MAX_OUTPUT_SIZE']
        }, {
            "name": "INFRABOX_JOB_MOUNT_DOCKER_SOCKET",
            "value": os.environ['INFRABOX_JOB_MOUNT_DOCKER_SOCKET']
        }, {
            "name": "INFRABOX_JOB_DAEMON_JSON",
            "value": self.daemon_json
        }, {
            "name": "INFRABOX_ROOT_URL",
            "value": os.environ['INFRABOX_ROOT_URL']
        }, {
            "name": "INFRABOX_JOB_TOKEN",
            "value": encode_job_token(job_id).decode()
        }, {
            "name": "INFRABOX_JOB_RESOURCES_LIMITS_MEMORY",
            "value": str(mem)
        }, {
            "name": "INFRABOX_JOB_RESOURCES_LIMITS_CPU",
            "value": str(cpu)
        }]

        if additional_env:
            env += additional_env

        if use_host_docker_daemon():
            volumes.append({
                "name": "docker-socket",
                "hostPath": {
                    "path": "/var/run/docker.sock",
                    "type": "Socket"
                }
            })

            volume_mounts.append({
                "mountPath": "/var/run/docker.sock",
                "name": "docker-socket"
            })

        if os.environ['INFRABOX_LOCAL_CACHE_ENABLED'] == 'true':
            volumes.append({
                "name": "local-cache",
                "hostPath": {
                    "path": os.environ['INFRABOX_LOCAL_CACHE_HOST_PATH']
                }
            })

            volume_mounts.append({
                "mountPath": "/local-cache",
                "name": "local-cache"
            })

        clone_volume_mounts = [{
            "mountPath": "/repo",
            "name": "repo"
        }]

        clone_env = [{
            "name": "INFRABOX_GENERAL_DONT_CHECK_CERTIFICATES",
            "value": os.environ['INFRABOX_GENERAL_DONT_CHECK_CERTIFICATES']
        }]

        if gerrit_enabled():
            gerrit_env = ({
                "name": "INFRABOX_GERRIT_HOSTNAME",
                "value": os.environ['INFRABOX_GERRIT_HOSTNAME']
            }, {
                "name": "INFRABOX_GERRIT_USERNAME",
                "value": os.environ['INFRABOX_GERRIT_USERNAME']
            }, {
                "name": "INFRABOX_GERRIT_PORT",
                "value": os.environ['INFRABOX_GERRIT_PORT']
            })

            env.extend(gerrit_env)
            clone_env.extend(gerrit_env)

            clone_volume_mounts.append({
                "name": "gerrit-ssh",
                "mountPath": "/tmp/gerrit/"
            })

            volumes.append({
                "name": "gerrit-ssh",
                "secret": {
                    "secretName": "infrabox-gerrit-ssh"
                }
            })

        run_job = {
            "kind": "Job",
            "apiVersion": "batch/v1",
            "metadata": {
                "name": job_id,
                "labels": {
                    "infrabox-job-type": "run-job",
                    "infrabox-job-id": job_id,
                    "infrabox-build-id": build_id
                }
            },
            "spec": {
                "template": {
                    "spec": {
                        "imagePullSecrets": [{"name": "infrabox-docker-secret"}],
                        "imagePullPolicy": "Always",
                        "automountServiceAccountToken": False,
                        "containers": [{
                            "name": "run-job",
                            "image": self.args.docker_registry + "/job:%s" % self.args.tag,
                            "command": ["/usr/local/bin/entrypoint.sh", "--type", job_type],

                            "securityContext": {
                                "privileged": True
                            },
                            "env": env,
                            "resources": {
                                "requests": {
                                    "cpu": cpu,
                                    "memory": "%sMi" % (mem + 256) # Some more memory for docker itself
                                },
                                "limits": {
                                    "cpu": cpu,
                                }
                            },
                            "volumeMounts": volume_mounts
                        }, {
                            "name": "git-clone",
                            "image": self.args.docker_registry + "/job-git:%s" % self.args.tag,
                            "env": clone_env,
                            "volumeMounts": clone_volume_mounts
                        }],
                        "restartPolicy": "OnFailure",
                        "volumes": volumes
                    }
                }
            }
        }

        r = requests.post(self.args.api_server + '/apis/batch/v1/namespaces/%s/jobs' % self.namespace,
                          headers=h, json=run_job, timeout=10)

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

        job_type = j[0]
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

        if job_type == 'create_job_matrix':
            job_type = 'create'
        elif job_type == "run_project_container" or job_type == "run_docker_compose":
            job_type = 'run'
        else:
            self.logger.error("Unknown job type: %s", job_type)
            return

        if not self.kube_job(job_id, build_id, cpu, memory, job_type, additional_env=additional_env):
            return

        cursor = self.conn.cursor()
        cursor.execute("UPDATE job SET state = 'scheduled' WHERE id = %s", [job_id])
        cursor.close()

        self.logger.info("Finished scheduling job")
        self.logger.info("")

        SCHEDULED_JOBS.inc()

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

            ABORTED_JOBS.inc()

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

            TIMEOUT_JOBS.inc()

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
                ORPHANED_NAMESPACES.inc()
                self.kube_delete_namespace(job_id)



    def handle_orphaned_jobs(self):
        h = {'Authorization': 'Bearer %s' % self.args.token}
        r = requests.get(self.args.api_server + '/apis/batch/v1/namespaces/%s/jobs' % self.namespace,
                         headers=h,
                         timeout=10)
        data = r.json()

        for j in data['items']:
            if 'metadata' not in j:
                continue

            metadata = j['metadata']
            if 'labels' not in metadata:
                continue

            labels = metadata['labels']

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

                self.logger.info('Deleting orphaned job %s', job_id)
                ORPHANED_JOBS.inc()
                self.kube_delete_job(job_id)

    @LOOP_SECONDS.time()
    def handle(self):
        try:
            self.handle_timeouts()
            self.handle_aborts()
            self.handle_orphaned_jobs()
            self.handle_orphaned_namespaces()
        except Exception as e:
            self.logger.exception(e)

        self.schedule()

    def run(self):
        daemon_json_path = '/etc/docker/daemon.json'
        if not os.path.exists(daemon_json_path):
            self.logger.error('%s does not exist', daemon_json_path)
            sys.exit(1)

        with open(daemon_json_path) as daemon_json:
            self.daemon_json = str(daemon_json.read())

        while True:
            is_leader(self.conn, "scheduler")
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
    get_env('INFRABOX_DATABASE_DB')
    get_env('INFRABOX_DATABASE_USER')
    get_env('INFRABOX_DATABASE_PASSWORD')
    get_env('INFRABOX_DATABASE_HOST')
    get_env('INFRABOX_DATABASE_PORT')
    get_env('INFRABOX_ROOT_URL')
    get_env('INFRABOX_DOCKER_REGISTRY_URL')
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

    start_http_server(8000)

    scheduler = Scheduler(conn, args)
    scheduler.run()

if __name__ == "__main__":
    try:
        main()
    except:
        print_stackdriver()
