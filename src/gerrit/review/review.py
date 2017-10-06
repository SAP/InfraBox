import json
import select

import psycopg2
import paramiko

from pyinfraboxutils import get_logger, get_env, print_stackdriver
from pyinfraboxutils.db import connect_db
from pyinfraboxutils.leader import elect_leader

logger = get_logger("gerrit")

def main():
    get_env('INFRABOX_SERVICE')
    get_env('INFRABOX_VERSION')
    get_env('INFRABOX_DATABASE_DB')
    get_env('INFRABOX_DATABASE_USER')
    get_env('INFRABOX_DATABASE_PASSWORD')
    get_env('INFRABOX_DATABASE_HOST')
    get_env('INFRABOX_DATABASE_PORT')
    get_env('INFRABOX_GERRIT_PORT')
    get_env('INFRABOX_GERRIT_HOSTNAME')
    get_env('INFRABOX_GERRIT_USERNAME')
    get_env('INFRABOX_GERRIT_KEY_FILENAME')
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
                logger.info(notify.payload)
                handle_job_update(conn, json.loads(notify.payload))

def execute_ssh_cmd(client, cmd):
    _, _, stderr = client.exec_command(cmd)
    err = stderr.read()
    if err:
        logger.error(err)


def handle_job_update(conn, update):
    if update['type'] != 'UPDATE':
        return

    if update['data']['project']['type'] != 'gerrit':
        return

    project_name = update['data']['project']['name']
    project_id = update['data']['project']['id']
    job_state = update['data']['job']['state']
    job_id = update['data']['job']['id']
    job_name = update['data']['job']['name']
    commit_sha = update['data']['commit']['id']
    build_id = update['data']['build']['id']

    if job_state in ('queued', 'scheduled'):
        return

    gerrit_port = int(get_env('INFRABOX_GERRIT_PORT'))
    gerrit_hostname = get_env('INFRABOX_GERRIT_HOSTNAME')
    gerrit_username = get_env('INFRABOX_GERRIT_USERNAME')
    gerrit_key_filename = get_env('INFRABOX_GERRIT_KEY_FILENAME')
    dashboard_url = get_env('INFRABOX_DASHBOARD_URL')

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(username=gerrit_username,
                   hostname=gerrit_hostname,
                   port=gerrit_port,
                   key_filename=gerrit_key_filename)
    client.get_transport().set_keepalive(60)
    logger.info("Connected to gerrit")

    message = "Job %s: %s\n%s/dashboard/project/%s/build/%s/job/%s/console" % (job_state,
                                                                               job_name,
                                                                               dashboard_url,
                                                                               project_id,
                                                                               build_id,
                                                                               job_id)

    c = conn.cursor()
    c.execute('''SELECT state, count(*) FROM job WHERE build_id = %s GROUP BY state''', [build_id])
    states = c.fetchall()
    c.close()

    vote = "0"
    if len(states) == 1 and states[0][0] == 'finished':
        # all finished
        vote = "+1"
    else:
        for s in states:
            if s[0] in ('running', 'scheduled', 'queued'):
                # still some running
                vote = "0"
                break
            elif s[0] != 'finished':
                # not successful
                vote = "-1"

    logger.info('Setting InfraBox=%s', vote)
    execute_ssh_cmd(client, 'gerrit review --project %s -m "%s" --label InfraBox=%s %s' % (project_name,
                                                                                           message,
                                                                                           vote,
                                                                                           commit_sha))

    client.close()

if __name__ == "__main__":
    try:
        main()
    except:
        print_stackdriver()
