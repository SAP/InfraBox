import json
import datetime

import paramiko

import psycopg2
import uuid

from pyinfraboxutils import get_logger, get_env
from pyinfraboxutils.db import connect_db
from pyinfraboxutils.leader import is_active

logger = get_logger("gerrit")

def main():
    get_env('INFRABOX_VERSION')
    get_env('INFRABOX_DATABASE_DB')
    get_env('INFRABOX_DATABASE_USER')
    get_env('INFRABOX_DATABASE_PASSWORD')
    get_env('INFRABOX_DATABASE_HOST')
    get_env('INFRABOX_DATABASE_PORT')
    gerrit_port = int(get_env('INFRABOX_GERRIT_PORT'))
    gerrit_hostname = get_env('INFRABOX_GERRIT_HOSTNAME')
    gerrit_username = get_env('INFRABOX_GERRIT_USERNAME')
    gerrit_key_filename = get_env('INFRABOX_GERRIT_KEY_FILENAME')

    cluster_name = get_env('INFRABOX_CLUSTER_NAME')

    conn = connect_db()
    logger.info("Connected to db")

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(username=gerrit_username,
                   hostname=gerrit_hostname,
                   port=gerrit_port,
                   key_filename=gerrit_key_filename)
    client.get_transport().set_keepalive(60)

    logger.info("Connected to gerrit")
    _, stdout, _ = client.exec_command('gerrit stream-events')

    logger.info("Waiting for stream-events")
    for line in stdout:
        for _ in range(0, 2):
            try:
                event = json.loads(line)

                if event['type'] in ("patchset-created", "draft-published", "change-merged"):
                    logger.debug(json.dumps(event, indent=4))
                    if not is_active(conn, cluster_name):
                        logger.info("cluster is inactive or disabled, skipping")
                        break
                    handle_patchset_created(conn, event)
                    break
            except psycopg2.IntegrityError:
                logger.info('duplicated key, skip this commit')
                try:
                    conn.close()
                except:
                    pass
                conn = connect_db()
                logger.info("reconnected to db")
                break
            except psycopg2.OperationalError:
                try:
                    conn.close()
                except:
                    pass

                conn = connect_db()
                logger.info("reconnected to db")


def handle_patchset_created_project(conn, event, project_id, project_name):
    if 'isDraft' in event['patchSet'] and event['patchSet']['isDraft']:
        return

    c = conn.cursor()
    c.execute('SELECT id FROM repository WHERE project_id = %s', [project_id])
    result = c.fetchone()
    c.close()

    repository_id = result[0]
    sha = event['patchSet']['revision']

    logger.info("Repository ID: %s", repository_id)

    c = conn.cursor()
    c.execute('SELECT * FROM "commit" WHERE project_id = %s and id = %s', [project_id, sha])
    result = c.fetchone()
    c.close()
    commit = result

    url = event['change']['url']

    # Abort all running builds for the same change
    c = conn.cursor()
    c.execute('''
        INSERT INTO abort
        SELECT j.id, null
        FROM job j
        JOIN build b
        ON b.id = j.build_id
        JOIN commit c
        ON b.commit_id = c.id
        AND b.project_id = c.project_id
        WHERE
            c.gerrit_change_id = %s AND
            j.state in ('scheduled', 'running') AND
            c.branch = %s
    ''', [event['change']['id'], event['change']['branch']])
    c.close()
    conn.commit()

    if not commit:
        url = event['change']['url'] 
        c = conn.cursor()
        c.execute('''
            INSERT INTO "commit" (
                id, message, repository_id, timestamp,
                author_name, author_email, author_username,
                committer_name, committer_email, committer_username, url, branch, project_id, tag, gerrit_change_id)
            VALUES (%s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s, %s, %s)
            RETURNING *
                ''', (sha, event['change']['commitMessage'],
                      repository_id, datetime.datetime.now(),
                      event['change']['owner'].get('name', 'unknown'),
                      '', event['change']['owner']['username'], '', '', '',
                      url,
                      event['change']['branch'], project_id, None, event['change']['id']))
        result = c.fetchone()
        c.close()
        commit = result

    c = conn.cursor()
    c.execute('''
        SELECT max(build_number) + 1 AS build_no
        FROM build AS b
        WHERE b.project_id = %s''', [project_id])
    result = c.fetchone()
    c.close()

    build_no = result[0]

    if not build_no:
        build_no = 1

    c = conn.cursor()
    c.execute('''INSERT INTO build (commit_id, build_number, project_id)
                 VALUES (%s, %s, %s)
                 RETURNING id''', (sha, build_no, project_id))
    result = c.fetchone()
    c.close()

    build_id = result[0]

    env_vars = {
        "GERRIT_PATCHSET_UPLOADER_USERNAME": event['patchSet']['uploader']['username'],
        "GERRIT_PATCHSET_UPLOADER_NAME": event['patchSet']['uploader'].get('name', ""),
        "GERRIT_PATCHSET_UPLOADER_EMAIL": event['patchSet']['uploader']['email'],
        "GERRIT_PATCHSET_NUMBER": event['patchSet']['number'],
        "GERRIT_PATCHSET_REF": event['patchSet']['ref'],
        "GERRIT_PATCHSET_REFSPEC": event['patchSet']['ref'],
        "GERRIT_PATCHSET_REVISION": event['patchSet']['revision'],

        "GERRIT_CHANGE_STATUS": event['change']['status'],
        "GERRIT_CHANGE_URL": event['change']['url'],
        "GERRIT_CHANGE_COMMIT_MESSAGE": event['change']['commitMessage'],
        "GERRIT_CHANGE_NUMBER": event['change']['number'],
        "GERRIT_CHANGE_PROJECT": event['change']['project'],
        "GERRIT_CHANGE_BRANCH": event['change']['branch'],
        "GERRIT_CHANGE_ID": event['change']['id'],
        "GERRIT_CHANGE_SUBJECT": event['change']['subject'],
        "GERRIT_CHANGE_OWNER_USERNAME": event['change']['owner']['username'],
        "GERRIT_CHANGE_OWNER_NAME": event['change']['owner'].get('name', ""),
        "GERRIT_CHANGE_OWNER_EMAIL": event['change']['owner']['email'],
        "GERRIT_CHNAGE_TOPIC": event['change'].get('topic', ""),

        "GERRIT_EVENT_TYPE": event['type'],

        # Jenkins compatibility
        "GERRIT_PROJECT": event['change']['project'],
        "GERRIT_BRANCH": event['change']['branch'],
        "GERRIT_REFSPEC": event['patchSet']['ref'],
        "GERRIT_TOPIC": event['change'].get('topic', ""),
        "GERRIT_HOST": get_env('INFRABOX_GERRIT_HOSTNAME'),
        "GERRIT_PORT": get_env('INFRABOX_GERRIT_PORT'),
    }

    if event.get('uploader', None):
        env_vars["GERRIT_UPLOADER_USERNAME"] = event['uploader']['username']
        env_vars["GERRIT_UPLOADER_NAME"] = event['uploader'].get('name', "")
        env_vars["GERRIT_UPLOADER_EMAIL"] = event['uploader']['email']

    if event.get('submitter', None):
        env_vars["GERRIT_SUBMITTER_USERNAME"] = event['submitter']['username']
        env_vars["GERRIT_SUBMITTER_NAME"] = event['submitter'].get('name', "")
        env_vars["GERRIT_SUBMITTER_EMAIL"] = event['submitter']['email']


    git_repo = {
        "commit": sha,
        "clone_url": "ssh://%s@%s:%s/%s" % (get_env('INFRABOX_GERRIT_USERNAME'),
                                            get_env('INFRABOX_GERRIT_HOSTNAME'),
                                            get_env('INFRABOX_GERRIT_PORT'),
                                            project_name),
        "ref": event['patchSet']['ref'],
        "event": event['change']['branch']
    }

    definition = {
        'build_only': False,
        'resources': {
            'limits': {
                'cpu': 0.5,
                'memory': 1024
            }
        }
    }

    c = conn.cursor()
    c.execute('''INSERT INTO job (id, state, build_id, type, name,
                                 project_id, dockerfile,
                                 repo, env_var, cluster_name, definition)
                VALUES (%s, 'queued', %s, 'create_job_matrix', 'Create Jobs',
                        %s, '', %s, %s, null, %s)''', (str(uuid.uuid5(uuid.NAMESPACE_DNS, (event['type'] + sha).encode('utf-8'))),
                                                       build_id,
                                                       project_id,
                                                       json.dumps(git_repo),
                                                       json.dumps(env_vars),
                                                       json.dumps(definition)))

def handle_patchset_created(conn, event):
    conn.rollback()

    project_name = event.get('project', None)

    if not project_name:
        project_name = event['change'].get('project', None)

    if not project_name:
        logger.error('Failed to get project from event')
        return


    logger.info("Project name: %s", project_name)

    # Get project
    c = conn.cursor()
    c.execute("SELECT id FROM project WHERE name = %s AND type='gerrit'", [project_name])
    projects = c.fetchall()
    c.close()

    logger.info("Found projects in db: %s", json.dumps(projects))

    if not projects:
        return

    for project in projects:
        project_id = project[0]
        logger.info("Handling project with id: %s", project_id)
        handle_patchset_created_project(conn, event, project_id, project_name)

    conn.commit()

if __name__ == "__main__":
    main()
