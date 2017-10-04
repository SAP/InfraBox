import json
import os
import logging
import traceback
import select
import time

import requests
import psycopg2

logging.basicConfig(
    format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%d-%m-%Y:%H:%M:%S',
    level=logging.INFO
)

logger = logging.getLogger("github")

def get_env(name): # pragma: no cover
    if name not in os.environ:
        raise Exception("%s not set" % name)
    return os.environ[name]

def connect_db(): # pragma: no cover
    while True:
        try:
            conn = psycopg2.connect(dbname=os.environ['INFRABOX_DATABASE_DB'],
                                    user=os.environ['INFRABOX_DATABASE_USER'],
                                    password=os.environ['INFRABOX_DATABASE_PASSWORD'],
                                    host=os.environ['INFRABOX_DATABASE_HOST'],
                                    port=os.environ['INFRABOX_DATABASE_PORT'])
            return conn
        except Exception as e:
            logger.warn("Could not connect to db: %s", e)
            time.sleep(3)

def elect_leader(): # pragma: no cover
    if os.environ.get('INFRABOX_DISABLE_LEADER_ELECTION', 'false') == 'true':
        return

    while True:
        r = requests.get("http://localhost:4040", timeout=5)
        leader = r.json()['name']

        if leader == os.environ['HOSTNAME']:
            logger.info("I'm the leader")
            break
        else:
            logger.info("I'm not the leader, %s is the leader", leader)
            time.sleep(1)

def execute_sql(conn, stmt, params): # pragma: no cover
    c = conn.cursor()
    c.execute(stmt, params)
    result = c.fetchall()
    c.close()
    return result

def main(): # pragma: no cover
    get_env('INFRABOX_SERVICE')
    get_env('INFRABOX_VERSION')
    get_env('INFRABOX_DATABASE_DB')
    get_env('INFRABOX_DATABASE_USER')
    get_env('INFRABOX_DATABASE_PASSWORD')
    get_env('INFRABOX_DATABASE_HOST')
    get_env('INFRABOX_DATABASE_PORT')
    get_env('INFRABOX_DASHBOARD_URL')

    elect_leader()

    conn = connect_db()
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    logger.info("Connected to database")

    curs = conn.cursor()
    curs.execute("LISTEN job_update;")

    logger.info("Waiting for job updates")

    while 1:
        if select.select([conn], [], [], 5) != ([], [], []):
            conn.poll()
            while conn.notifies:
                notify = conn.notifies.pop(0)
                handle_job_update(conn, json.loads(notify.payload))


def handle_job_update(conn, update):
    if update['data']['project']['type'] != 'github':
        return

    project_id = update['data']['project']['id']
    job_state = update['data']['job']['state']
    job_id = update['data']['job']['id']
    job_name = update['data']['job']['name']
    commit_sha = update['data']['commit']['id']
    build_id = update['data']['build']['id']
    dashboard_url = get_env('INFRABOX_DASHBOARD_URL')

    # determine github commit state
    state = 'success'
    if job_state in ('scheduled', 'running', 'queued'):
        state = 'pending'

    if job_state in ('failure', 'skipped', 'killed'):
        state = 'failure'

    if job_state == 'error':
        state = 'error'

    logger.info("")
    logger.info("Handle job %s", job_id)
    logger.info("Setting state to %s", state)

    token = execute_sql(conn, '''
        SELECT github_api_token FROM "user" u
        INNER JOIN collaborator co
            ON co.owner = true
            AND co.project_id = %s
            AND co.user_id = u.id
    ''', [project_id])

    if not token:
        logger.info("No API token, not updating status")
        return

    github_api_token = token[0][0]

    github_status_url = execute_sql(conn, '''
        SELECT github_status_url
        FROM "commit"
        WHERE id = %s
        AND project_id = %s
    ''', [commit_sha, project_id])[0][0]

    payload = {
        "state": state,
        "target_url":  dashboard_url + \
                       '/dashboard/project/' + \
                       project_id + '/build/' + \
                       build_id + '/job/' + job_id,
        "description": "InfraBox",
        "context": "Job: %s" % job_name
    }

    headers = {
        "Authorization": "token " + github_api_token,
        "User-Agent": "InfraBox"
    }

    # TODO(ib-steffen): support ca bundles
    r = requests.post(github_status_url,
                      data=json.dumps(payload),
                      headers=headers,
                      timeout=5,
                      verify=False)

    if r.status_code != 201:
        logger.warn("Failed to update github status: %s", r.text)
    else:
        logger.info("Successfully updated github status")


def print_stackdriver(): # pragma: no cover
    if 'INFRABOX_GENERAL_LOG_STACKDRIVER' in os.environ and \
            os.environ['INFRABOX_GENERAL_LOG_STACKDRIVER'] == 'true':
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

if __name__ == "__main__": # pragma: no cover
    try:
        main()
    except:
        print_stackdriver()
