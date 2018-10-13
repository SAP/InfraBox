# pylint: disable=too-few-public-methods,line-too-long,too-many-lines,too-many-nested-blocks
import argparse
import time
import os
import random
import json
import copy
from datetime import datetime

import requests

import psycopg2
import psycopg2.extensions

from pyinfraboxutils import get_logger, get_env
from pyinfraboxutils.db import connect_db
from pyinfraboxutils.token import encode_job_token

class APIException(Exception):
    def __init__(self, result):
        super(APIException, self).__init__("API Server Error (%s)" % result.status_code)
        self.result = result

class Controller(object):
    def __init__(self, args, resource):
        self.args = args
        self.namespace = get_env("INFRABOX_GENERAL_WORKER_NAMESPACE")
        self.logger = get_logger("controller")
        self.resource = resource

    def _get(self, url):
        h = {'Authorization': 'Bearer %s' % self.args.token}
        self.logger.info('GET: %s', url)
        r = requests.get(url, headers=h, timeout=10)
        # self.logger.info(r.text)

        if r.status_code == 404:
            return None

        if r.status_code != 200:
            raise APIException(r)

        result = r.json()
        return result

    def _update(self, url, data):
        h = {'Authorization': 'Bearer %s' % self.args.token}
        self.logger.info('PUT: %s', url)
        r = requests.put(url, headers=h, json=data, timeout=10)
        # self.logger.info(r.text)

        if r.status_code != 200:
            raise APIException(r)

        result = r.json()
        return result

    def _create(self, url, data):
        h = {'Authorization': 'Bearer %s' % self.args.token}
        self.logger.info('POST: %s', url)
        r = requests.post(url, headers=h, json=data, timeout=10)
        # self.logger.info(r.text)

        if r.status_code == 409:
            # Already exists
            return None

        if r.status_code != 201:
            raise APIException(r)

        result = r.json()
        return result

    def _delete(self, url):
        h = {'Authorization': 'Bearer %s' % self.args.token}
        self.logger.info('DELETE: %s', url)
        r = requests.delete(url, headers=h, timeout=10)
        # self.logger.info(r.text)

        if r.status_code == 404:
            # does not exist
            return None

        if r.status_code != 200:
            raise APIException(r)

        result = r.json()
        return result

    def _update_finalizer(self, fi, finalizers):
        if fi['metadata'].get('finalizers', None):
            return fi

        fi['metadata']['finalizers'] = finalizers
        url = self._get_url(fi)
        return self._update(url, fi)

    def _get_url(self, fi):
        url = '%s/apis/core.infrabox.net/v1alpha1/namespaces/%s/%s/%s' % (self.args.api_server,
                                                                          self.namespace,
                                                                          self.resource,
                                                                          fi['metadata']['name'])
        return url

    def handle(self):
        url = '%s/apis/core.infrabox.net/v1alpha1/namespaces/%s/%s' % (self.args.api_server,
                                                                       self.namespace,
                                                                       self.resource)
        data = self._get(url)

        if 'items' not in data:
            return

        for fi in data['items']:
            try:
                before = json.dumps(fi.get('status', {})) + json.dumps(fi['metadata'].get('finalizers', {}))
                if fi['metadata'].get('deletionTimestamp', None):
                    fi = self._sync_delete(fi)
                else:
                    fi = self._sync(fi)

                url = self._get_url(fi)
                after = json.dumps(fi.get('status', {})) + json.dumps(fi['metadata'].get('finalizers', {}))

                if before != after:
                    self._update(url, fi)
            except APIException as e:
                self.logger.exception(e)
                self.logger.warn(e.result.text)
            except Exception as e:
                self.logger.exception(e)

    def _sync(self, _):
        assert False

    def _sync_delete(self, _):
        assert False

class PipelineInvocationController(Controller):
    def __init__(self, args):
        super(PipelineInvocationController, self).__init__(args, 'ibpipelineinvocations')
        self.pipelines = {}

    def _get_pipeline(self, pi):
        if pi['spec']['pipelineName'] not in self.pipelines:
            url = '%s/apis/core.infrabox.net/v1alpha1/namespaces/%s/ibpipelines/%s' % (self.args.api_server,
                                                                                       pi['metadata']['namespace'],
                                                                                       pi['spec']['pipelineName'])
            self.pipelines[pi['spec']['pipelineName']] = self._get(url)

        return copy.deepcopy(self.pipelines[pi['spec']['pipelineName']])

    def _delete_services(self, pi):
        services = pi['spec'].get('services', [])

        if not services:
            return

        for i, s in enumerate(services):
            name = '%s-%s' % (pi['metadata']['name'], i)
            url = '%s/apis/%s/namespaces/%s/%s/%s' % (self.args.api_server,
                                                      s['apiVersion'],
                                                      self.namespace,
                                                      s['kind'].lower() + 's',
                                                      name)
            self._delete(url)

    def _are_services_deleted(self, pi):
        services = pi['spec'].get('services', [])

        if not services:
            return True

        for i, s in enumerate(services):
            name = '%s-%s' % (pi['metadata']['name'], i)
            url = '%s/apis/%s/namespaces/%s/%s/%s' % (self.args.api_server,
                                                      s['apiVersion'],
                                                      self.namespace,
                                                      s['kind'].lower() + 's',
                                                      name)


            try:
                self._get(url)
            except:
                return False

        return True


    def _sync_delete(self, pi):
        self._delete_services(pi)

        pipeline = self._get_pipeline(pi)
        for step in pipeline['spec']['steps']:
            name = pi['metadata']['name'] + '-' + step['name']
            url = '%s/apis/core.infrabox.net/v1alpha1/namespaces/%s/ibfunctioninvocations/%s' % (self.args.api_server,
                                                                                                 pi['metadata']['namespace'],
                                                                                                 name)
            self._delete(url)

        pi['metadata']['finalizers'] = []
        return pi

    def _sync_services(self, pi):
        services = pi['spec'].get('services', [])

        ready = True
        if not services:
            return ready

        for i, s in enumerate(services):
            name = '%s-%s' % (pi['metadata']['name'], i)

            service = {
                'apiVersion': s['apiVersion'],
                'kind': s['kind'],
                'metadata': {
                    'name': name,
                    'namespace': pi['metadata']['namespace'],
                    'annotations': s['metadata'].get('annotations', {}),
                    'labels': {
                        'service.infrabox.net/secret-name': name
                    }
                },
                'spec': s['spec']
            }

            url = '%s/apis/%s/namespaces/%s/%s' % (self.args.api_server,
                                                   s['apiVersion'],
                                                   pi['metadata']['namespace'],
                                                   s['kind'].lower() + 's')
            self._create(url, service)

            url = '%s/apis/%s/namespaces/%s/%s/%s' % (self.args.api_server,
                                                      s['apiVersion'],
                                                      pi['metadata']['namespace'],
                                                      s['kind'].lower() + 's',
                                                      name)

            service = self._get(url)

            status = service.get('status', {}).get('status', False)
            if status == 'ready':
                continue
            elif status == 'error':
                # TODO
                pass
            else:
                ready = False

        return ready

    def _sync_prepare(self, pi):
        pi['status']['message'] = 'Services are being created'
        pi['status']['state'] = 'preparing'
        pi = self._update_finalizer(pi, ['core.service.infrabox.net'])

        ready = self._sync_services(pi)
        if ready:
            pi['status']['message'] = ''
            pi['status']['state'] = 'scheduling'

        return pi

    def _sync_run(self, pi):
        p = self._get_pipeline(pi)

        for i, step in enumerate(p['spec']['steps']):
            if not pi['status'].get('stepStatuses', None):
                pi['status']['stepStatuses'] = []

            if len(pi['status']['stepStatuses']) <= i:
                pi['status']['stepStatuses'].append({
                    'state': {
                        'waiting': {
                            'message': 'Containers are being created'
                        }
                    }
                })

            status = pi['status']['stepStatuses'][i]

            if status['state'].get('terminated', None):
                # already finished
                continue

            step_invocation = pi['spec']['steps'][step['name']]

            fi_name = pi['metadata']['name'] + '-' + step['name']
            fi = {
                'apiVersion': 'core.infrabox.net/v1alpha1',
                'kind': 'IBFunctionInvocation',
                'metadata': {
                    'name': fi_name,
                    'namespace': pi['metadata']['namespace']
                },
                'spec': {
                    'functionName': step['functionName'],
                    'env': step_invocation['env'],
                    'volumes': [],
                    'volumeMounts': []
                }
            }

            if step_invocation.get('resources', None):
                fi['spec']['resources'] = step_invocation['resources']

            if pi['spec'].get('services', None):
                for j, s in enumerate(pi['spec']['services']):
                    name = '%s-%s' % (pi['metadata']['name'], j)
                    fi['spec']['volumes'] += [{
                        'name': name,
                        'secret': {
                            'secretName': name
                        }
                    }]

                    fi['spec']['volumeMounts'] += [{
                        'name':  name,
                        'mountPath': '/var/run/infrabox.net/services/' + s['metadata']['name']
                    }]

            url = '%s/apis/core.infrabox.net/v1alpha1/namespaces/%s/ibfunctioninvocations/' % (self.args.api_server,
                                                                                               self.namespace)
            self._create(url, fi)

            url = '%s/apis/core.infrabox.net/v1alpha1/namespaces/%s/ibfunctioninvocations/%s' % (self.args.api_server,
                                                                                                 self.namespace,
                                                                                                 fi_name)

            fi = self._get(url)

            if fi.get('status', None):
                pi['status']['stepStatuses'][i] = fi['status']

                if fi['status'].get('state', {}).get('terminated', None):
                    break

        first_state = pi['status']['stepStatuses'][0].get('state', {})

        if first_state.get('running', None):
            pi['status']['message'] = ""
            pi['status']['state'] = "running"
            pi['status']['startTime'] = first_state['running']['startedAt']
        elif first_state.get('terminated', None):
            pi['status']['message'] = ""
            pi['status']['state'] = "running"
            pi['status']['startTime'] = first_state['terminated']['startedAt']

        all_terminated = True

        for step_status in pi['status']['stepStatuses']:
            if not step_status.get('state', {}).get('terminated', None):
                all_terminated = False

        if all_terminated:
            pi['status']['message'] = ""
            pi['status']['state'] = "finalizing"
            pi['status']['startTime'] = first_state['terminated']['startedAt']
            pi['status']['completionTime'] = pi['status']['stepStatuses'][-1]['state']['terminated']['finishedAt']

        return pi

    def _sync_finalize(self, pi):
        self._delete_services(pi)

        deleted = self._are_services_deleted(pi)
        if not deleted:
            return pi

        pi['status']['message'] = ''
        pi['status']['state'] = 'terminated'
        return pi

    def _sync(self, pi):
        if not pi.get('status', None):
            pi['status'] = {
                'stepStatuses': []
            }

        state = pi['status'].get('state', None)
        if state in ('error', 'terminated'):
            return pi

        if state in (None, '', 'preparing'):
            pi = self._sync_prepare(pi)

        if state in ('running', 'scheduling'):
            pi = self._sync_run(pi)

        if state == 'finalizing':
            pi = self._sync_finalize(pi)

        return pi

class FunctionInvocationController(Controller):
    def __init__(self, args):
        super(FunctionInvocationController, self).__init__(args, 'ibfunctioninvocations')
        self.functions = {}

    def _get_function(self, fi):
        if fi['spec']['functionName'] not in self.functions:
            url = '%s/apis/core.infrabox.net/v1alpha1/namespaces/%s/ibfunctions/%s' % (self.args.api_server,
                                                                                       self.namespace,
                                                                                       fi['spec']['functionName'])
            self.functions[fi['spec']['functionName']] = self._get(url)

        return copy.deepcopy(self.functions[fi['spec']['functionName']])

    def _sync_delete(self, fi):
        url = '%s/apis/batch/v1/namespaces/%s/jobs/%s' % (self.args.api_server,
                                                          self.namespace,
                                                          fi['metadata']['name'])
        self._delete(url)

        url = '%s/api/v1/namespaces/%s/pods?labelSelector=function.infrabox.net/function-invocation-name=%s' % (self.args.api_server,
                                                                                                                self.namespace,
                                                                                                                fi['metadata']['name'])
        pods = self._get(url)
        for pod in pods['items']:
            url = '%s/api/v1/namespaces/%s/pods/%s' % (self.args.api_server,
                                                       self.namespace,
                                                       pod['metadata']['name'])
            self._delete(url)

        fi['metadata']['finalizers'] = []
        return fi

    def _sync(self, fi):
        if not fi.get('status', None):
            fi['status'] = {}

        fi = self._update_finalizer(fi, ['core.service.infrabox.net'])
        f = self._get_function(fi)

        # Create a batch job
        job = {
            'name': 'function',
            'imagePullPolicy': 'Always',
            'image': f['spec']['image'],
            'resources': f['spec']['resources'],
            'env': f['spec']['env'],
            'securityContext': f['spec']['securityContext'],
            'volumeMounts': f['spec']['volumeMounts'],
        }

        job['volumeMounts'] += fi['spec'].get('volumeMounts', [])
        job['env'] += fi['spec'].get('env', [])

        if fi['spec'].get('resources', None):
            job['resources'] = fi['spec']['resources']

        containers = [job]

        batch = {
            'Kind': 'Job',
            'apiVersion': 'batch/v1',
            'metadata': {
                'name': fi['metadata']['name'],
                'namespace': fi['metadata']['namespace'],
                'labels': {
                    'function.infrabox.net/function-invocation-name':  fi['metadata']['name']
                }
            },
            'spec': {
                'template': {
                    'spec': {
                        'automountServiceAccountToken': False,
                        'containers': containers,
                        'restartPolicy': 'Never',
                        'terminationGracePeriodSeconds': 0,
                        'volumes': f['spec']['volumes'],
                        'imagePullSecrets': f['spec'].get('imagePullSecrets', None)
                    },
                    'metadata': {
                        'labels': {
                            'function.infrabox.net/function-invocation-name':  fi['metadata']['name']
                        }
                    }
                },
                'completion': 1,
                'parallelism': 1,
                'backoffLimit': 0
            }
        }

        batch['spec']['template']['spec']['volumes'] += fi['spec'].get('volumes', [])

        url = '%s/apis/batch/v1/namespaces/%s/jobs/' % (self.args.api_server,
                                                        self.namespace)
        self._create(url, batch)

        # Sync status
        url = '%s/api/v1/namespaces/%s/pods?labelSelector=function.infrabox.net/function-invocation-name=%s' % (self.args.api_server,
                                                                                                                self.namespace,
                                                                                                                fi['metadata']['name'])
        pods = self._get(url)
        for pod in pods['items']:
            if pod['status'].get('containerStatuses', None):
                fi['status']['state'] = pod['status']['containerStatuses'][0]['state']
                fi['status']['nodeName'] = pod['spec']['nodeName']
            elif pod['status']['phase'] == 'Failed':
                fi['status']['state'] = {
                    'terminated': {
                        'exitCode': 200,
                        'reason': pod['status'].get('reason', None),
                        'message': pod['status'].get('message', None)
                    }
                }

        return fi

class Scheduler(object):
    def __init__(self, conn, args):
        self.conn = conn
        self.args = args
        self.namespace = get_env("INFRABOX_GENERAL_WORKER_NAMESPACE")
        self.logger = get_logger("scheduler")
        self.function_controller = FunctionInvocationController(args)
        self.pipeline_controller = PipelineInvocationController(args)

    def handle_function_invocations(self):
        self.function_controller.handle()

    def handle_pipeline_invocations(self):
        self.pipeline_controller.handle()

    def kube_delete_job(self, job_id):
        h = {'Authorization': 'Bearer %s' % self.args.token}

        url = '%s/apis/core.infrabox.net/v1alpha1/namespaces/%s/ibpipelineinvocations/%s' % (self.args.api_server,
                                                                                             self.namespace,
                                                                                             job_id)

        try:
            r = requests.get(url, headers=h, timeout=5)
            job = r.json()

            if job['metadata'].get('deletionTimestamp', None):
                # Already marked for deletion, don't delete again to not for an update in the controller
                return

            requests.delete(url, headers=h, timeout=5)
        except:
            pass

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
            SELECT definition FROM job j WHERE j.id = %s
        ''', (job_id,))
        j = cursor.fetchone()
        cursor.close()

        definition = j[0]

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
            SELECT j.id, j.type, j.dependencies, j.definition
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
            job_type = j[1]
            dependencies = j[2]
            definition = j[3]

            limits = {}
            if definition:
                limits = definition.get('resources', {}).get('limits', {})

            memory = limits.get('memory', 1024)
            cpu = limits.get('cpu', 1)

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
                DELETE FROM "abort" RETURNING job_id, user_id
            ), jobs_to_abort AS (
                SELECT j.id, j.state, user_id FROM all_aborts
                JOIN job j
                    ON all_aborts.job_id = j.id
                    AND j.state not in ('finished', 'failure', 'error', 'killed')
                    AND cluster_name = %s
            )

            SELECT id, user_id FROM jobs_to_abort WHERE state in ('scheduled', 'running', 'queued')
        ''', [cluster_name])

        aborts = cursor.fetchall()
        cursor.close()

        for abort in aborts:
            job_id = abort[0]
            user_id = abort[1]
            self.kube_delete_job(job_id)
            self.upload_console(job_id)

            if user_id:
                cursor = self.conn.cursor()
                cursor.execute("""
                    SELECT username
                    FROM "user"
                    WHERE id = %s
                """, [user_id])
                user = cursor.fetchone()
                cursor.close()
                message = 'Aborted by %s' % user[0]
            else:
                message = 'Aborted'

            # Update state
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE job
                SET state = 'killed',
                    end_date = current_timestamp,
                    message = %s
                WHERE id = %s AND state IN ('scheduled', 'running', 'queued')
            """, [message, job_id])
            cursor.close()

    def handle_timeouts(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT j.id FROM job j
            WHERE j.start_date < (NOW() - (CASE
                                           WHEN j.definition->>'timeout' is not null THEN (j.definition->>'timeout')::integer * INTERVAL '1' SECOND
                                           ELSE INTERVAL '3600' SECOND
                                           END
                                          )
                                 )
            AND j.state = 'running'
        ''')
        aborts = cursor.fetchall()
        cursor.close()

        for abort in aborts:
            job_id = abort[0]
            self.kube_delete_job(job_id)
            self.upload_console(job_id)

            # Update state
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE job SET state = 'error', end_date = current_timestamp, message = 'Aborted due to timeout'
                WHERE id = %s""", (job_id,))
            cursor.close()

    def upload_console(self, job_id):
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

        cursor = self.conn.cursor()
        cursor.execute("""
            DELETE FROM console WHERE job_id = %s
        """, [job_id])
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
            if last_state in ('killed', 'finished', 'error', 'failure'):
                self.kube_delete_job(job_id)
                continue

            start_date = None
            end_date = None
            delete_job = False
            current_state = last_state
            message = None
            node_name = None

            if j.get('status', None):
                status = j['status']
                s = status.get('state', "preparing")
                message = status.get('message', None)

                if s in ["preparing", "scheduling"] and last_state in ["queued", "scheduled"]:
                    current_state = 'scheduled'

                if s in ["running", "finalizing"]:
                    current_state = 'running'

                if s == "terminated":
                    current_state = 'error'

                    if 'stepStatuses' in status and status['stepStatuses']:
                        stepStatus = status['stepStatuses'][-1]
                        exit_code = stepStatus['state']['terminated']['exitCode']

                        if exit_code == 0:
                            current_state = 'finished'
                        else:
                            current_state = 'failure'
                            message = stepStatus['state']['terminated'].get('message', None)

                            if not message:
                                message = stepStatus['state']['terminated'].get('reason', 'Unknown Error')

                    if not message and current_state != 'finished':
                        self.logger.error(json.dumps(status, indent=4))

                    delete_job = True

                if message == 'Error':
                    self.logger.error(json.dumps(status, indent=4))

                if s == "error":
                    current_state = 'error'
                    delete_job = True
                    start_date = datetime.now()
                    end_date = datetime.now()

                if 'stepStatuses' in status and status['stepStatuses']:
                    stepStatus = status['stepStatuses'][-1]
                    nn = stepStatus.get('nodeName', None)

                    if nn:
                        # don't overwrite existing node name with none
                        node_name = nn

                start_date = status.get('startTime', None)
                end_date = status.get('completionTime', None)

            if last_state == current_state:
                continue

            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE job SET
                    state = %s,
                    start_date = %s,
                    end_date = %s,
                    message = %s,
                    node_name = %s
                WHERE id = %s
            """, (current_state, start_date, end_date, message, node_name, job_id))
            cursor.close()

            if delete_job:
                self.upload_console(job_id)
                self.logger.info('Deleting job %s', job_id)
                self.kube_delete_job(job_id)

    def get_default_cluster(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name, labels
            FROM cluster
            WHERE active = true AND
                  enabled = true
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
        cursor.execute("begin;")
        cursor.execute("""
            UPDATE job
            SET cluster_name = %s
            WHERE cluster_name is null
        """, [cluster_name])

        cursor.execute("commit;")
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
            metadata = i.get('metadata', {})
            l = metadata.get('labels', {})
            master = l.get('node-role.kubernetes.io/master', "false")

            if master == "true":
                continue

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
            SET last_update = NOW(), labels = %s, root_url = %s, nodes = %s, cpu_capacity = %s, memory_capacity = %s
            WHERE cluster.name = %s """, [cluster_name, labels, root_url, nodes, cpu, memory, labels,
                                          root_url, nodes, cpu, memory, cluster_name])
        cursor.close()

    def _inactive(self):
        cluster_name = os.environ['INFRABOX_CLUSTER_NAME']
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT active, enabled
            FROM cluster
            WHERE name = %s """, [cluster_name])
        active, enabled = cursor.fetchone()
        cursor.close()

        return not (active and enabled)

    def handle(self):
        self.update_cluster_state()

        try:
            self.handle_function_invocations()
            self.handle_pipeline_invocations()
            self.handle_timeouts()
            self.handle_aborts()
            self.handle_orphaned_jobs()
        except Exception as e:
            self.logger.exception(e)

        cluster_name = os.environ['INFRABOX_CLUSTER_NAME']
        ha_mode = os.environ['INFRABOX_HA_ENABLED'] == "true"

        if self._inactive():
            self.logger.info('Cluster set to inactive or disabled, sleeping...')
            time.sleep(5)
            return

        if ha_mode:
            self.assign_cluster()
        elif cluster_name == 'master':
            self.assign_cluster()

        self.schedule()

    def run(self):
        self.logger.info("Starting scheduler")

        while True:
            self.handle()
            time.sleep(1)

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
