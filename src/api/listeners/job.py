import json

from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from eventlet.hubs import trampoline

from pyinfraboxutils import get_logger
from pyinfraboxutils.db import connect_db

logger = get_logger('job_listener')

def __handle_event(event, socketio):
    build_id = event['data']['build']['id']
    project_id = event['data']['project']['id']
    socketio.emit('notify:job', event, room=build_id)
    socketio.emit('notify:job', event, room=project_id)

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
