import json

from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from eventlet.hubs import trampoline

from pyinfraboxutils.db import connect_db
from pyinfraboxutils import dbpool
from pyinfraboxutils import get_logger

logger = get_logger('console_listener')

def __handle_event(event, socketio, client_manager):
    job_id = event['job_id']
    console_id = event['id']

    if not client_manager.has_clients(job_id):
        return

    logger.debug('start console %s', console_id)
    conn = dbpool.get()
    try:
        r = conn.execute_one('''
           SELECT output FROM console WHERE id = %s
        ''', [console_id])
        logger.debug('retrived console %s', console_id)

        if not r:
            return

        r = r[0]

        socketio.emit('notify:console', {
            'data': r,
            'job_id': job_id
        }, room=job_id)
    finally:
        dbpool.put(conn)
        logger.debug('stop console %s', console_id)

def listen(socketio, client_manager):
    while True:
        try:
            __listen(socketio, client_manager)
        except Exception as e:
            logger.exception(e)

def __listen(socketio, client_manager):
    conn = connect_db()
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute("LISTEN console_update")

    while True:
        trampoline(conn, read=True)
        conn.poll()
        while conn.notifies:
            n = conn.notifies.pop()
            socketio.start_background_task(__handle_event,
                                           json.loads(n.payload),
                                           socketio,
                                           client_manager)
