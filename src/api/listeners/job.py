import json

from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from eventlet.hubs import trampoline

from pyinfraboxutils import get_logger
from pyinfraboxutils.db import connect_db
from pyinfraboxutils import dbpool

logger = get_logger('job_listener')

def __handle_event(event, socketio):
    job_id = event['job_id']

    db = dbpool.get()

    try:
        job = db.execute_one_dict('''
            SELECT id, state, to_char(start_date, 'YYYY-MM-DD HH24:MI:SS') start_date, type, dockerfile,
                   to_char(end_date, 'YYYY-MM-DD HH24:MI:SS') end_date,
                   name, dependencies, to_char(created_at, 'YYYY-MM-DD HH24:MI:SS') created_at, message,
                   project_id, build_id, node_name, avg_cpu, definition, restarted
            FROM job
            WHERE id = %s
        ''', [job_id])

        if not job:
            return

        project_id = job['project_id']
        build_id = job['build_id']

        project = db.execute_one_dict('''
            SELECT id, name, type
            FROM project
            WHERE id = %s
        ''', [project_id])

        if not project:
            return

        build = db.execute_one_dict('''
            SELECT id, build_number, restart_counter, commit_id, is_cronjob
            FROM build
            WHERE id = %s
        ''', [build_id])

        commit_id = build['commit_id']

        commit = None
        pr = None
        if project['type'] in ('gerrit', 'github'):
            commit = db.execute_one_dict('''
                SELECT
                            c.id,
                            split_part(c.message, '\n', 1) as message,
                            c.author_name,
                            c.author_email,
                            c.author_username,
                            c.committer_name,
                            c.committer_email,
                            c.committer_username,
                            c.url,
                            c.branch,
                            c.pull_request_id
                FROM commit c
                WHERE c.id = %s
                AND   c.project_id = %s
            ''', [commit_id, project_id])

            pull_request_id = commit['pull_request_id']

            pr = db.execute_one_dict('''
                SELECT title, url
                FROM pull_request
                WHERE id = %s
                AND   project_id = %s
            ''', [pull_request_id, project_id])

    finally:
        dbpool.put(db)

    msg = {
        'type': event['type'],
        'data': {
            'build': build,
            'project': project,
            'commit': commit,
            'pull_request': pr,
            'job': job
        }
    }

    socketio.emit('notify:job', msg, room=build_id)
    socketio.emit('notify:job', msg, room=project_id)

def listen(socketio):
    while True:
        try:
            __listen(socketio)
        except Exception as e:
            logger.exception(e)

def __listen(socketio):
    conn = connect_db()
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute("LISTEN job_update")

    while True:
        trampoline(conn, read=True)
        conn.poll()
        while conn.notifies:
            n = conn.notifies.pop()
            socketio.start_background_task(__handle_event,
                                           json.loads(n.payload),
                                           socketio)
