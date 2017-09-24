import time
import os
import json
import traceback
import logging
import psycopg2
import psycopg2.extensions
import requests
from prometheus_client import start_http_server, Gauge

FORMAT = '%(asctime)-15s %(levelno)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.ERROR)
logger = logging.getLogger("scheduler")

# pylint: disable=no-value-for-parameter, no-member
JOBS_RUNNING = Gauge('infrabox_jobs_running', 'Jobs with state running')
JOBS_SCHEDULED = Gauge('infrabox_jobs_scheduled', 'Jobs with state scheduled')
JOBS_QUEUED = Gauge('infrabox_jobs_queued', 'Jobs with state queued')
JOBS_FINISHED = Gauge('infrabox_jobs_finished', 'Jobs with state finished')
JOBS_KILLED = Gauge('infrabox_jobs_killed', 'Jobs with state killed')
JOBS_ERROR = Gauge('infrabox_jobs_error', 'Jobs with state error')
JOBS_FAILURE = Gauge('infrabox_jobs_failure', 'Jobs with state failure')
JOBS_SKIPPED = Gauge('infrabox_jobs_skipped', 'Jobs with state skipped')

def get_jobs(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT count(*), state FROM job GROUP BY state')
    result = cursor.fetchall()
    cursor.close()

    print result

    JOBS_RUNNING.set(0)
    JOBS_SCHEDULED.set(0)
    JOBS_QUEUED.set(0)
    JOBS_FINISHED.set(0)
    JOBS_KILLED.set(0)
    JOBS_ERROR.set(0)

    for r in result:
        count = r[0]
        state = r[1]

        if state == 'running':
            JOBS_RUNNING.set(count)

        if state == 'scheduled':
            JOBS_SCHEDULED.set(count)

        if state == 'queued':
            JOBS_QUEUED.set(count)

        if state == 'finished':
            JOBS_FINISHED.set(count)

        if state == 'killed':
            JOBS_KILLED.set(count)

        if state == 'error':
            JOBS_ERROR.set(count)

JOBS_CPU_REQUESTED = Gauge('infrabox_jobs_cpu_requested_total', 'Total requested CPU of all jobs', ['state'])
JOBS_MEMORY_REQUESTED = Gauge('infrabox_jobs_memory_requsted_bytes_total', 'Total requested memory of all jobs', ['state'])

def get_active_resources(conn):
    cursor = conn.cursor()
    cursor.execute('''SELECT state, sum(cpu), sum(memory) from job group by state having state in ('running', 'scheduled')''')
    result = cursor.fetchall()
    cursor.close()

    for state in ('running', 'scheduled'):
        JOBS_CPU_REQUESTED.labels(state=state).set(0)
        JOBS_MEMORY_REQUESTED.labels(state=state).set(0)

    for r in result:
        state = r[0]
        cpu = r[1]
        memory = r[2] * 1024 * 1024

        JOBS_CPU_REQUESTED.labels(state=state).set(cpu)
        JOBS_MEMORY_REQUESTED.labels(state=state).set(memory)


K8S_NODE_CPU = Gauge('infrabox_k8s_node_cpu_cores', 'CPU cores per node', ['hostname'])
K8S_NODE_MEMORY = Gauge('infrabox_k8s_node_memory_bytes', 'Memory per node', ['hostname'])

def get_k8s_stats():
    with open('/var/run/secrets/kubernetes.io/serviceaccount/token', 'r') as f:
        token = f.read()

        h = {'Authorization': 'Bearer %s' % token}
        api_server = "https://" + get_env('INFRABOX_KUBERNETES_MASTER_HOST') + ":" + get_env('INFRABOX_KUBERNETES_MASTER_PORT')

        r = requests.get(api_server + '/api/v1/nodes', headers=h, timeout=5).json()

        for node in r['items']:
            hostname = None

            for a in node['status']['addresses']:
                if a['type'] == "Hostname":
                    hostname = a['address']
                    break

            capa = node['status']['capacity']
            cpu = capa['cpu']
            memory = capa['memory']
            memory = int(memory[:-2]) * 1024

            K8S_NODE_CPU.labels(hostname=hostname).set(cpu)
            K8S_NODE_MEMORY.labels(hostname=hostname).set(memory)


def get_env(name):
    if name not in os.environ:
        raise Exception("%s not set" % name)
    return os.environ[name]


def main():
    get_env('INFRABOX_SERVICE')
    get_env('INFRABOX_VERSION')
    get_env('INFRABOX_DATABASE_DB')
    get_env('INFRABOX_DATABASE_USER')
    get_env('INFRABOX_DATABASE_PASSWORD')
    get_env('INFRABOX_DATABASE_HOST')
    get_env('INFRABOX_DATABASE_PORT')
    get_env('INFRABOX_KUBERNETES_MASTER_HOST')
    get_env('INFRABOX_KUBERNETES_MASTER_PORT')

    while True:
        r = requests.get("http://localhost:4040", timeout=5)
        leader = r.json()['name']

        if leader == os.environ['HOSTNAME']:
            logger.info("I'm the leader")
            break
        else:
            logger.info("I'm not the leader, %s is the leader", leader)
            time.sleep(1)

    conn = psycopg2.connect(dbname=os.environ['INFRABOX_DATABASE_DB'],
                            user=os.environ['INFRABOX_DATABASE_USER'],
                            password=os.environ['INFRABOX_DATABASE_PASSWORD'],
                            host=os.environ['INFRABOX_DATABASE_HOST'],
                            port=os.environ['INFRABOX_DATABASE_PORT'])

    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    os.environ['REQUESTS_CA_BUNDLE'] = '/var/run/secrets/kubernetes.io/serviceaccount/ca.crt'

    start_http_server(8000)

    while True:
        get_jobs(conn)
        get_active_resources(conn)
        get_k8s_stats()
        time.sleep(1)

def print_stackdriver():
    if 'INFRABOX_GENERAL_LOG_STACKDRIVER' in os.environ and os.environ['INFRABOX_GENERAL_LOG_STACKDRIVER'] == 'true':
        print json.dumps({
            "serviceContext": {
                "service": os.environ.get('INFRABOX_SERVICE', 'unknown'),
                "version": os.environ.get('INFRABOX_VERSION', 'unknown')
            },
            "message": traceback.format_exc(),
            "severity": 'ERROR'
        })
    else:
        print traceback.format_exc()

if __name__ == "__main__":
    try:
        main()
    except:
        print_stackdriver()
