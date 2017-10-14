import logging
import argparse
import time
import os
import psycopg2
import psycopg2.extensions
import requests
from prometheus_client import start_http_server, Histogram, Counter

from pyinfraboxutils import get_logger, get_env, print_stackdriver
from pyinfraboxutils.leader import elect_leader
from pyinfraboxutils.db import connect_db

logger = get_logger("scheduler")

namespace = 'infrabox-worker'

# pylint: disable=no-value-for-parameter
LOOP_SECONDS = Histogram('infrabox_scheduler_loop_seconds', 'Time spent for one scheduler loop iteration')
ORPHANED_JOBS = Counter('infrabox_scheduler_orphaned_jobs_total', 'Number of removed orphaned jobs')
ABORTED_JOBS = Counter('infrabox_scheduler_killed_jobs_total', 'Number of killed jobs')
SCHEDULED_JOBS = Counter('infrabox_scheduler_scheduled_jobs_total', 'Number of scheduled jobs')
TIMEOUT_JOBS = Counter('infrabox_scheduler_timeout_jobs_total', 'Number of timed out scheduled jobs')

def use_gcs():
    return os.environ['INFRABOX_STORAGE_GCS_ENABLED'] == 'true'

def use_s3():
    return os.environ['INFRABOX_STORAGE_S3_ENABLED'] == 'true'

def gerrit_enabled():
    return os.environ['INFRABOX_GERRIT_ENABLED'] == 'true'

class Scheduler(object):
    def __init__(self, conn, args):
        self.conn = conn
        self.args = args

    def get_database_env(self):
        env = ({
            "name": "INFRABOX_DATABASE_USER",
            "valueFrom": {
                "secretKeyRef": {
                    "name": "infrabox-postgres",
                    "key": "username"
                }
            }
        }, {
            "name": "INFRABOX_DATABASE_PASSWORD",
            "valueFrom": {
                "secretKeyRef": {
                    "name": "infrabox-postgres",
                    "key": "password"
                }
            }
        }, {
            "name": "INFRABOX_DATABASE_HOST",
            "value": os.environ['INFRABOX_DATABASE_HOST']
        }, {
            "name": "INFRABOX_DATABASE_DB",
            "value": os.environ['INFRABOX_DATABASE_DB']
        }, {
            "name": "INFRABOX_DATABASE_PORT",
            "value": os.environ['INFRABOX_DATABASE_PORT']
        })

        return env

    def get_api_server_container(self, job_id):
        env = [{
            "name": "INFRABOX_JOB_ID",
            "value": job_id
        }, {
            "name": "INFRABOX_SERVICE",
            "value": "job-api"
        }, {
            "name": "INFRABOX_VERSION",
            "value": self.args.tag
        }, {
            "name": "INFRABOX_GENERAL_NO_CHECK_CERTIFICATES",
            "value": os.environ['INFRABOX_GENERAL_NO_CHECK_CERTIFICATES']
        }, {
            "name": "INFRABOX_DASHBOARD_URL",
            "value": os.environ['INFRABOX_DASHBOARD_URL']
        }, {
            "name": "INFRABOX_STORAGE_GCS_ENABLED",
            "value": os.environ['INFRABOX_STORAGE_GCS_ENABLED']
        }, {
            "name": "INFRABOX_STORAGE_S3_ENABLED",
            "value": os.environ['INFRABOX_STORAGE_S3_ENABLED']
        }, {
            "name": "INFRABOX_JOB_MAX_OUTPUT_SIZE",
            "value": os.environ['INFRABOX_JOB_MAX_OUTPUT_SIZE']
        }, {
            "name": "INFRABOX_GERRIT_ENABLED",
            "value": os.environ['INFRABOX_GERRIT_ENABLED']
        }]

        if use_gcs():
            env.extend(({
                "name": "INFRABOX_STORAGE_GCS_CONTAINER_OUTPUT_BUCKET",
                "value": os.environ['INFRABOX_STORAGE_GCS_CONTAINER_OUTPUT_BUCKET']
            }, {
                "name": "INFRABOX_STORAGE_GCS_CONTAINER_CONTENT_CACHE_BUCKET",
                "value": os.environ['INFRABOX_STORAGE_GCS_CONTAINER_CONTENT_CACHE_BUCKET']
            }, {
                "name": "INFRABOX_STORAGE_GCS_PROJECT_UPLOAD_BUCKET",
                "value": os.environ['INFRABOX_STORAGE_GCS_PROJECT_UPLOAD_BUCKET']
            }))

        if use_s3():
            env.extend(({
                "name": "INFRABOX_STORAGE_S3_CONTAINER_OUTPUT_BUCKET",
                "value": os.environ['INFRABOX_STORAGE_S3_CONTAINER_OUTPUT_BUCKET']
            }, {
                "name": "INFRABOX_STORAGE_S3_CONTAINER_CONTENT_CACHE_BUCKET",
                "value": os.environ['INFRABOX_STORAGE_S3_CONTAINER_CONTENT_CACHE_BUCKET']
            }, {
                "name": "INFRABOX_STORAGE_S3_PROJECT_UPLOAD_BUCKET",
                "value": os.environ['INFRABOX_STORAGE_S3_PROJECT_UPLOAD_BUCKET']
            }, {
                "name": "INFRABOX_STORAGE_S3_ENDPOINT",
                "value": os.environ['INFRABOX_STORAGE_S3_ENDPOINT']
            }, {
                "name": "INFRABOX_STORAGE_S3_PORT",
                "value": os.environ['INFRABOX_STORAGE_S3_PORT']
            }, {
                "name": "INFRABOX_STORAGE_S3_ACCESS_KEY",
                "value": os.environ['INFRABOX_STORAGE_S3_ACCESS_KEY']
            }, {
                "name": "INFRABOX_STORAGE_S3_SECRET_KEY",
                "value": os.environ['INFRABOX_STORAGE_S3_SECRET_KEY']
            }, {
                "name": "INFRABOX_STORAGE_S3_REGION",
                "value": os.environ['INFRABOX_STORAGE_S3_REGION']
            }, {
                "name": "INFRABOX_STORAGE_S3_SECURE",
                "value": os.environ['INFRABOX_STORAGE_S3_SECURE']
            }))

        db_env = self.get_database_env()
        env.extend(db_env)

        r = {
            "name": "job-api",
            "image": self.args.docker_registry + "/infrabox/job-api:%s" % self.args.tag,
            "env": env,
            "resources": {
                "requests": {
                    "memory": "256Mi",
                    "cpu": 0.1
                },
                "limits": {
                    "memory": "256Mi",
                    "cpu": 0.1
                }
            },
            "volumeMounts": []
        }

        if use_gcs():
            r["volumeMounts"].append({
                "name": "gcs-service-account",
                "mountPath": "/etc/infrabox/gcs",
                "readOnly": True
            })

        return r

    def kube_delete_job(self, job_id):
        h = {'Authorization': 'Bearer %s' % self.args.token}

        # find pods which belong to the job
        p = {"labelSelector": "job-name=%s" % job_id}
        r = requests.get(self.args.api_server + '/api/v1/namespaces/%s/pods' % (namespace,),
                         headers=h, params=p, timeout=5)
        pods = r.json()

        # delete the job
        p = {"gracePeriodSeconds": 0}
        requests.delete(self.args.api_server + '/apis/batch/v1/namespaces/%s/jobs/%s' % (namespace, job_id,),
                        headers=h, params=p, timeout=5)

        # If there are no pods it is already set to None
        # so we check it before the loop
        if not pods.get('items', None):
            return

        # delete all pods
        for pod in pods.get('items', []):
            pod_name = pod['metadata']['name']

            p = {"gracePeriodSeconds": 0}
            requests.delete(self.args.api_server + '/api/v1/namespaces/%s/pods/%s' % (namespace, pod_name,),
                            headers=h, params=p, timeout=5)

    def kube_job(self, job_id, build_id, cpu, mem, job_type):
        h = {'Authorization': 'Bearer %s' % self.args.token}
        volumes = [{
            "name": "data-dir",
            "emptyDir": {}
        }, {
            "name": "analyzer-tmp",
            "emptyDir": {}
        }, {
            "name": "dockerd-config",
            "configMap": {
                "name": "infrabox-dockerd-config"
            }
        }]

        volume_mounts = [{
            "mountPath": "/data",
            "name": "data-dir"
        }, {
            "mountPath": "/tmp",
            "name": "analyzer-tmp"
        }, {
            "mountPath": "/etc/docker",
            "name": "dockerd-config"
        }]

        env = [{
            "name": "INFRABOX_JOB_ID",
            "value": job_id
        }, {
            "name": "INFRABOX_GENERAL_NO_CHECK_CERTIFICATES",
            "value": os.environ['INFRABOX_GENERAL_NO_CHECK_CERTIFICATES']
        }, {
            "name": "INFRABOX_API_SERVER",
            "value": "localhost:5000"
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
            "name": "INFRABOX_CLAIR_ENABLED",
            "value": os.environ['INFRABOX_CLAIR_ENABLED']
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
            "name": "INFRABOX_DOCKER_REGISTRY_ADMIN_USERNAME",
            "valueFrom": {
                "secretKeyRef": {
                    "name": "infrabox-docker-registry",
                    "key": "username"
                }
            }
        }, {
            "name": "INFRABOX_DOCKER_REGISTRY_ADMIN_PASSWORD",
            "valueFrom": {
                "secretKeyRef": {
                    "name": "infrabox-docker-registry",
                    "key": "password"
                }
            }
        }, {
            "name": "INFRABOX_DASHBOARD_URL",
            "value": os.environ['INFRABOX_DASHBOARD_URL']
        }]

        if use_gcs():
            volumes.append({
                "name": "gcs-service-account",
                "secret": {
                    "secretName": "infrabox-gcs"
                }
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

        if gerrit_enabled():
            env.extend(({
                "name": "INFRABOX_GERRIT_HOSTNAME",
                "value": os.environ['INFRABOX_GERRIT_HOSTNAME']
            }, {
                "name": "INFRABOX_GERRIT_USERNAME",
                "value": os.environ['INFRABOX_GERRIT_USERNAME']
            }, {
                "name": "INFRABOX_GERRIT_PORT",
                "value": os.environ['INFRABOX_GERRIT_PORT']
            }))

            volume_mounts.append({
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
                        "containers": [self.get_api_server_container(job_id), {
                            "name": "run-job",
                            "image": self.args.docker_registry + "/infrabox/job:%s" % self.args.tag,
                            "command": ["/usr/local/bin/wait-for-webserver.sh", "localhost:5000",
                                        "/usr/local/bin/entrypoint.sh", "--type", job_type],

                            "securityContext": {
                                "privileged": True
                            },
                            "env": env,
                            "resources": {
                                "requests": {
                                    "cpu": cpu,
                                    "memory": "%sMi" % mem
                                },
                                "limits": {
                                    "cpu": cpu,
                                    "memory": "%sMi" % mem
                                }
                            },
                            "volumeMounts": volume_mounts
                        }],
                        "restartPolicy": "OnFailure",
                        "volumes": volumes
                    }
                }
            }
        }

        db_env = self.get_database_env()

        if os.environ['INFRABOX_CLAIR_ENABLED'] == "true":
            clair_container = {
                "name": "clair",
                "image": self.args.docker_registry + "/infrabox/clair/analyzer:%s" % self.args.tag,
                "env": db_env,
                "resources": {
                    "requests": {
                        "memory": "256Mi",
                        "cpu": 0.2
                    },
                    "limits": {
                        "memory": "256Mi",
                        "cpu": 0.2
                    }
                },
                "volumeMounts": [{
                    "mountPath": "/var/lib/docker",
                    "name": "data-dir"
                }, {
                    "mountPath": "/tmp",
                    "name": "analyzer-tmp"
                }]
            }

            run_job['spec']['template']['spec']['containers'].append(clair_container)

        if os.environ['INFRABOX_STORAGE_CLOUDSQL_ENABLED'] == "true":
            cloudsql_container = {
                "image": "gcr.io/cloudsql-docker/gce-proxy:1.09",
                "name": "cloudsql-proxy",
                "command": ["/cloud_sql_proxy", "--dir=/cloudsql",
                            "-instances="
                            + os.environ['INFRABOX_STORAGE_CLOUDSQL_INSTANCE_CONNECTION_NAME']
                            + "=tcp:5432",
                            "-credential_file=/secrets/cloudsql/credentials.json"],
                "resources": {
                    "requests": {
                        "memory": "256Mi",
                        "cpu": 0.1
                    },
                    "limits": {
                        "memory": "256Mi",
                        "cpu": 0.1
                    }
                },
                "volumeMounts": [{
                    "name": "cloudsql-instance-credentials",
                    "mountPath": "/secrets/cloudsql",
                    "readOnly": True
                }, {
                    "name": "ssl-certs",
                    "mountPath": "/etc/ssl/certs"
                }, {
                    "name": "cloudsql",
                    "mountPath": "/cloudsql"
                }]
            }

            run_job['spec']['template']['spec']['containers'].append(cloudsql_container)
            volumes = [{
                "name": "cloudsql-instance-credentials",
                "secret": {
                    "secretName": "infrabox-cloudsql-instance-credentials"
                }
            }, {
                "name": "ssl-certs",
                "hostPath": {
                    "path": "/etc/ssl/certs"
                }
            }, {
                "name": "cloudsql",
                "emptyDir": {}
            }]

            run_job['spec']['template']['spec']['volumes'].extend(volumes)

        r = requests.post(self.args.api_server + '/apis/batch/v1/namespaces/%s/jobs' % namespace,
                          headers=h, json=run_job, timeout=5)

        return r.status_code == 201

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
            cpu = cpu * 0.7
        else:
            cpu = cpu * 0.9

        logger.info("Scheduling job to kubernetes")

        if job_type == 'create_job_matrix':
            job_type = 'create'
        elif job_type == "run_project_container" or job_type == "run_docker_compose":
            job_type = 'run'
        else:
            logger.error("Unknown job type: %s", job_type)
            return

        if not self.kube_job(job_id, build_id, cpu, memory, job_type):
            return

        cursor = self.conn.cursor()
        cursor.execute("UPDATE job SET state = 'scheduled' WHERE id = %s", [job_id])
        cursor.close()

        logger.info("Finished scheduling job")
        logger.info("")

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
                continue

            # If it's a wait job we are done here
            if job_type == "wait":
                logger.info("Wait job, we are done")
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


    def handle_orphaned_jobs(self):
        h = {'Authorization': 'Bearer %s' % self.args.token}
        r = requests.get(self.args.api_server + '/apis/batch/v1/namespaces/%s/jobs' % namespace, headers=h, timeout=5)
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

                logger.warn('Deleting orphaned job %s', job_id)
                ORPHANED_JOBS.inc()
                self.kube_delete_job(job_id)

    @LOOP_SECONDS.time()
    def handle(self):
        try:
            self.handle_timeouts()
            self.handle_aborts()
            self.handle_orphaned_jobs()
        except:
            pass

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

    if args.loglevel == 'debug':
        logger.setLevel(logging.DEBUG)
    elif args.loglevel == 'info':
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.INFO)

    get_env('INFRABOX_SERVICE')
    get_env('INFRABOX_VERSION')
    get_env('INFRABOX_STORAGE_CLOUDSQL_ENABLED')
    get_env('INFRABOX_DATABASE_DB')
    get_env('INFRABOX_DATABASE_USER')
    get_env('INFRABOX_DATABASE_PASSWORD')
    get_env('INFRABOX_DATABASE_HOST')
    get_env('INFRABOX_DATABASE_PORT')
    get_env('INFRABOX_DASHBOARD_URL')
    get_env('INFRABOX_DOCKER_REGISTRY_URL')
    get_env('INFRABOX_CLAIR_ENABLED')
    get_env('INFRABOX_STORAGE_GCS_ENABLED')
    get_env('INFRABOX_STORAGE_S3_ENABLED')
    get_env('INFRABOX_GENERAL_NO_CHECK_CERTIFICATES')
    get_env('INFRABOX_JOB_MAX_OUTPUT_SIZE')
    get_env('INFRABOX_JOB_MOUNT_DOCKER_SOCKET')

    if use_gcs():
        get_env('INFRABOX_STORAGE_GCS_CONTAINER_OUTPUT_BUCKET')
        get_env('INFRABOX_STORAGE_GCS_CONTAINER_CONTENT_CACHE_BUCKET')
        get_env('INFRABOX_STORAGE_GCS_PROJECT_UPLOAD_BUCKET')

    if use_s3():
        get_env('INFRABOX_STORAGE_S3_CONTAINER_CONTENT_CACHE_BUCKET')
        get_env('INFRABOX_STORAGE_S3_CONTAINER_OUTPUT_BUCKET')
        get_env('INFRABOX_STORAGE_S3_PROJECT_UPLOAD_BUCKET')
        get_env('INFRABOX_STORAGE_S3_ENDPOINT')
        get_env('INFRABOX_STORAGE_S3_PORT')
        get_env('INFRABOX_STORAGE_S3_ACCESS_KEY')
        get_env('INFRABOX_STORAGE_S3_SECRET_KEY')
        get_env('INFRABOX_STORAGE_S3_REGION')
        get_env('INFRABOX_STORAGE_S3_SECURE')

    if get_env('INFRABOX_GERRIT_ENABLED') == 'true':
        get_env('INFRABOX_GERRIT_USERNAME')
        get_env('INFRABOX_GERRIT_HOSTNAME')
        get_env('INFRABOX_GERRIT_PORT')

    # try to read from filesystem
    with open('/var/run/secrets/kubernetes.io/serviceaccount/token', 'r') as f:
        args.token = f.read()

    elect_leader()

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
