import json
import select
import os

import urllib
import requests
import psycopg2
import eventlet
eventlet.monkey_patch()
from eventlet.hubs import trampoline

import urllib3
urllib3.disable_warnings()

from pyinfraboxutils import get_logger, get_env, get_root_url
from pyinfraboxutils.db import connect_db
from pyinfraboxutils.leader import elect_leader, is_leader, is_active
from pyinfraboxutils import dbpool

logger = get_logger("github")

def execute_sql(conn, stmt, params): # pragma: no cover
    c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    c.execute(stmt, params)
    result = c.fetchall()
    c.close()
    return result

def main(): # pragma: no cover
    get_env('INFRABOX_VERSION')
    get_env('INFRABOX_DATABASE_DB')
    get_env('INFRABOX_DATABASE_USER')
    get_env('INFRABOX_DATABASE_PASSWORD')
    get_env('INFRABOX_DATABASE_HOST')
    get_env('INFRABOX_DATABASE_PORT')

    cluster_name = get_env('INFRABOX_CLUSTER_NAME')
    conn = connect_db()
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    logger.info("Connected to database")

    elect_leader(conn, 'github-review', cluster_name)

    curs = conn.cursor()
    curs.execute("LISTEN job_update;")

    logger.info("Waiting for job updates")
    pool = eventlet.GreenPool()

    while True:
        trampoline(conn, read=True)
        conn.poll()
        while conn.notifies:
            notify = conn.notifies.pop(0)
            event = json.loads(notify.payload)
            if not is_leader(conn, 'github-review', cluster_name, exit=False):
                logger.info("skip job: %s because I'm not leader", event.get('job_id'))
                continue
            pool.spawn_n(handle, event)


def handle(event):
    db = dbpool.get()
    try:
        handle_job_update(db.conn, event)
    except Exception as e:
        logger.error(e)
    finally:
        dbpool.put(db)


def handle_job_update(conn, event):
    job_id = event['job_id']

    jobs = execute_sql(conn, '''
        SELECT id, state, name, project_id, build_id
        FROM job
        WHERE id = %s
    ''', [job_id])

    if not jobs:
        return False

    job = jobs[0]

    project_id = job['project_id']
    build_id = job['build_id']

    projects = execute_sql(conn, '''
        SELECT id, name, type
        FROM project
        WHERE id = %s
    ''', [project_id])

    if not projects:
        return False

    project = projects[0]

    if project['type'] != 'github':
        return False

    builds = execute_sql(conn, '''
        SELECT id, build_number, restart_counter, commit_id
        FROM build
        WHERE id = %s
    ''', [build_id])

    if not builds:
        return False

    build = builds[0]

    project_name = project['name']
    job_state = job['state']
    job_name = job['name']
    commit_sha = build['commit_id']
    build_id = build['id']
    build_number = build['build_number']
    build_restartCounter = build['restart_counter']

    # determine github commit state
    state = 'success'
    if job_state in ('scheduled', 'running', 'queued'):
        state = 'pending'

    if job_state in ('failure', 'skipped', 'killed', 'unstable'):
        state = 'failure'

    if job_state == 'error':
        state = 'error'

    logger.info("")
    logger.info("Handle job %s", job_id)
    logger.info("Setting jobs %s state to %s", job_id, state)

    token = execute_sql(conn, '''
        SELECT github_api_token FROM "user" u
        INNER JOIN collaborator co
            ON co.role = 'Owner'
            AND co.project_id = %s
            AND co.user_id = u.id
    ''', [project_id])

    if not token:
        logger.warn("No API token, not updating status")
        return False

    github_api_token = token[0]['github_api_token']

    github_status_url = execute_sql(conn, '''
        SELECT github_status_url
        FROM "commit"
        WHERE id = %s
        AND project_id = %s
    ''', [commit_sha, project_id])[0]['github_status_url']

    ha_mode = os.environ.get('INFRABOX_HA_ENABLED') == 'true'
    if ha_mode:
        dashboard_url = get_root_url('global')
    else:
        dashboard_url = execute_sql(conn, '''
                    SELECT root_url
                    FROM cluster
                    WHERE name = 'master'
                ''', [])[0]['root_url']

    target_url = '%s/dashboard/#/project/%s/build/%s/%s/job/%s' % (dashboard_url,
                                                                   urllib.quote(project_name, safe=''),
                                                                   build_number,
                                                                   build_restartCounter,
                                                                   urllib.quote_plus(job_name).replace('+', '%20'))

    job_name = job_name.split(".")[0]
    payload = {
        "state": state,
        "target_url": target_url,
        "description": "project_id:%s job_id:%s" % (project_id, job_id),
        "context": "Job: %s" % job_name
    }

    headers = {
        "Authorization": "token " + github_api_token,
        "User-Agent": "InfraBox"
    }

    # TODO(ib-steffen): support ca bundles
    try:
        r = requests.post(github_status_url,
                          data=json.dumps(payload),
                          headers=headers,
                          timeout=10,
                          verify=False)

        if r.status_code != 201:
            logger.warn("[job: %s] Failed to update github status: %s", job_id, r.text)
            logger.warn(github_status_url)
        else:
            logger.info("[job: %s] Successfully updated github status", job_id)
    except Exception as e:
        logger.warn("[job: %s] Failed to update github status: %s", job_id, e)
        return False

    return True

if __name__ == "__main__": # pragma: no cover
    main()
