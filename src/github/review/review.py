import json
import select

import requests
import psycopg2

from pyinfraboxutils import get_logger, print_stackdriver, get_env
from pyinfraboxutils.db import connect_db
from pyinfraboxutils.leader import elect_leader

logger = get_logger("github")

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


    conn = connect_db()
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    logger.info("Connected to database")

    elect_leader(conn, "github-review")

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

if __name__ == "__main__": # pragma: no cover
    try:
        main()
    except:
        print_stackdriver()
