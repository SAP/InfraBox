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

# pylint: disable=no-value-for-parameter
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

JOBS_SCHEDULED_CPU = Gauge('infrabox_jobs_scheduled_cpu_total', 'Total CPU of all jobs in state scheduled')
JOBS_SCHEDULED_MEMORY = Gauge('infrabox_jobs_scheduled_memory_total', 'Total Memory of all jobs in state scheduled')

JOBS_RUNNING_CPU = Gauge('infrabox_jobs_running_cpu_total', 'Total CPU of all jobs in state running')
JOBS_RUNNING_MEMORY = Gauge('infrabox_jobs_running_memory_total', 'Total Memory of all jobs in state running')

def get_active_resources(conn):
    cursor = conn.cursor()
    cursor.execute('''SELECT state, sum(cpu), sum(memory) from job group by state having state in ('running', 'scheduled')''')
    result = cursor.fetchall()
    cursor.close()

    JOBS_SCHEDULED_CPU.set(0)
    JOBS_SCHEDULED_MEMORY.set(0)
    JOBS_RUNNING_CPU.set(0)
    JOBS_RUNNING_MEMORY.set(0)

    for r in result:
        state = r[0]
        cpu = r[1]
        memory = r[2]

        if state == 'running':
            JOBS_RUNNING_CPU.set(cpu)
            JOBS_RUNNING_MEMORY.set(memory)

        if state == 'scheduled':
            JOBS_SCHEDULED_CPU.set(cpu)
            JOBS_SCHEDULED_MEMORY.set(memory)

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

    start_http_server(8000)

    while True:
        get_jobs(conn)
        get_active_resources(conn)
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
