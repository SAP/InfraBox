import json
import os
import logging
import traceback
import select
import time

import requests
import psycopg2
import paramiko

FORMAT = '%(asctime)-15s %(levelno)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger("gerrit")

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
    get_env('INFRABOX_GERRIT_PORT')
    get_env('INFRABOX_GERRIT_HOSTNAME')
    get_env('INFRABOX_GERRIT_USERNAME')
    get_env('INFRABOX_GERRIT_KEY_FILENAME')
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
    execute_ssh_cmd(client, 'gerrit review --project %s -m "%s" --label InfraBox=%s %s' % (project_name, message, vote, commit_sha))

    client.close()

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
