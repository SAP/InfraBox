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

def get_env(name):
    if name not in os.environ:
        raise Exception("%s not set" % name)
    return os.environ[name]

def main():
    get_env('INFRABOX_SERVICE')
    get_env('INFRABOX_VERSION')
    pg_db = get_env('INFRABOX_DATABASE_DB')
    pg_user = get_env('INFRABOX_DATABASE_USER')
    pg_password = get_env('INFRABOX_DATABASE_PASSWORD')
    pg_host = get_env('INFRABOX_DATABASE_HOST')
    pg_port = int(get_env('INFRABOX_DATABASE_PORT'))
    get_env('INFRABOX_DASHBOARD_URL')

    while True:
        r = requests.get("http://localhost:4040", timeout=5)
        leader = r.json()['name']

        if leader == os.environ['HOSTNAME']:
            logger.info("I'm the leader")
            break
        else:
            logger.info("I'm not the leader, %s is the leader", leader)
            time.sleep(1)

    conn = psycopg2.connect(dbname=pg_db,
                            user=pg_user,
                            password=pg_password,
                            host=pg_host,
                            port=pg_port)
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

    c = conn.cursor()
    c.execute('''
        SELECT github_api_token FROM "user" u
        INNER JOIN collaborator co
            ON co.owner = true
            AND co.project_id = %s
            AND co.user_id = u.id
    ''', [project_id])
    token = c.fetchall()
    c.close()

    if not token:
        logger.info("No API token, not updating status")
        return

    github_api_token = token[0][0]

    c = conn.cursor()
    c.execute('''
        SELECT github_status_url
        FROM "commit"
        WHERE id = %s
        AND project_id = %s
    ''', [commit_sha, project_id])
    github_status_url = c.fetchall()[0][0]
    c.close()

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


def print_stackdriver():
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

if __name__ == "__main__":
    try:
        main()
    except:
        print_stackdriver()
