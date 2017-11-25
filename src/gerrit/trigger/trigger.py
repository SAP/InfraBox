import json
import datetime

import paramiko

from pyinfraboxutils import get_logger, get_env, print_stackdriver
from pyinfraboxutils.leader import elect_leader, is_leader
from pyinfraboxutils.db import connect_db

logger = get_logger("gerrit")

def main():
    get_env('INFRABOX_SERVICE')
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

    conn = connect_db()
    logger.info("Connected to db")

    elect_leader(conn, "gerrit-trigger")

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
        event = json.loads(line)
        is_leader(conn, "gerrit-trigger")

        if event['type'] == "patchset-created":
            logger.info(json.dumps(event, indent=4))
            handle_patchset_created(conn, event)

def handle_patchset_created_project(conn, event, project_id, project_name):
    if event['patchSet']['isDraft']:
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

    if not commit:
        c = conn.cursor()
        c.execute('''
            INSERT INTO "commit" (
                id, message, repository_id, timestamp,
                author_name, author_email, author_username,
                committer_name, committer_email, committer_username, url, branch, project_id, tag)
            VALUES (%s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s, %s)
            RETURNING *
                ''', (sha, event['change']['commitMessage'],
                      repository_id, datetime.datetime.now(),
                      event['change']['owner']['name'],
                      '', event['change']['owner']['username'], '', '', '',
                      event['change']['url'],
                      event['change']['branch'], project_id, None))
        result = c.fetchone()
        c.close()
        commit = result

    print commit

    c = conn.cursor()
    c.execute('''SELECT count(distinct build_number) + 1 AS build_no
              FROM build AS b
              WHERE b.project_id = %s''', [project_id])
    result = c.fetchone()
    c.close()

    build_no = result[0]
    c = conn.cursor()
    c.execute('''INSERT INTO build (commit_id, build_number, project_id)
                 VALUES (%s, %s, %s)
                 RETURNING id''', (sha, build_no, project_id))
    result = c.fetchone()
    c.close()

    build_id = result[0]

    env_vars = {
        "INFRABOX_GERRIT_PATCHSET_UPLOADER_USERNAME": event['patchSet']['uploader']['username'],
        "INFRABOX_GERRIT_PATCHSET_UPLOADER_NAME": event['patchSet']['uploader']['name'],
        "INFRABOX_GERRIT_PATCHSET_UPLOADER_EMAIL": event['patchSet']['uploader']['email'],
        "INFRABOX_GERRIT_PATCHSET_REF": event['patchSet']['ref'],
        "INFRABOX_GERRIT_PATCHSET_REVISION": event['patchSet']['revision'],
        "INFRABOX_GERRIT_CHANGE_STATUS": event['change']['status'],
        "INFRABOX_GERRIT_CHANGE_URL": event['change']['url'],
        "INFRABOX_GERRIT_CHANGE_COMMIT_MESSAGE": event['change']['commitMessage'],
        "INFRABOX_GERRIT_CHANGE_NUMBER": event['change']['number'],
        "INFRABOX_GERRIT_CHANGE_PROJECT": event['change']['project'],
        "INFRABOX_GERRIT_CHANGE_BRANCH": event['change']['branch'],
        "INFRABOX_GERRIT_CHANGE_ID": event['change']['id'],
        "INFRABOX_GERRIT_CHANGE_SUBJECT": event['change']['subject'],
        "INFRABOX_GERRIT_CHANGE_OWNER_USERNAME": event['change']['owner']['username'],
        "INFRABOX_GERRIT_CHANGE_OWNER_NAME": event['change']['owner']['name'],
        "INFRABOX_GERRIT_CHANGE_OWNER_EMAIL": event['change']['owner']['email'],
        "INFRABOX_GERRIT_UPLOADER_USERNAME": event['uploader']['username'],
        "INFRABOX_GERRIT_UPLOADER_NAME": event['uploader']['name'],
        "INFRABOX_GERRIT_UPLOADER_EMAIL": event['uploader']['email']
    }

    git_repo = {
        "commit": sha,
        "clone_url": "ssh://%s@%s:%s/%s" % (get_env('INFRABOX_GERRIT_USERNAME'),
                                            get_env('INFRABOX_GERRIT_HOSTNAME'),
                                            get_env('INFRABOX_GERRIT_PORT'),
                                            project_name),
        "ref": event['patchSet']['ref'],
        "event": event['change']['branch']
    }

    c = conn.cursor()
    c.execute('''INSERT INTO job (id, state, build_id, type, name,
                                 project_id, build_only, dockerfile,
                                 cpu, memory, repo, env_var)
                VALUES (gen_random_uuid(), 'queued', %s, 'create_job_matrix', 'Create Jobs',
                        %s, false, '', 1, 1024, %s, %s)''', (build_id,
                                                             project_id,
                                                             json.dumps(git_repo),
                                                             json.dumps(env_vars)))

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
    try:
        main()
    except:
        print_stackdriver()
