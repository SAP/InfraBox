import os
import uuid

import eventlet
eventlet.monkey_patch()

import flask_socketio
import socketio

from flask import jsonify

from pyinfraboxutils import get_env, print_stackdriver, get_logger
from pyinfraboxutils.ibrestplus import app, api
from pyinfraboxutils.ibflask import get_token, is_collaborator
from pyinfraboxutils import dbpool

# TODO: do it the same way in api
import dashboard_api.handlers

import dashboard_api.listeners.job
import dashboard_api.listeners.console

logger = get_logger('dashboard-api')

# TODO: Move to common
class ClientManager(socketio.base_manager.BaseManager):
    def __init__(self):
        super(ClientManager, self).__init__()
        self.__rooms = {}

    def enter_room(self, sid, namespace, room):
        super(ClientManager, self).enter_room(sid, namespace, room)
        logger.debug('%s joined room %s', sid, room)

        if room not in self.__rooms:
            self.__rooms[room] = 0

        self.__rooms[room] += 1

    def leave_room(self, sid, namespace, room):
        super(ClientManager, self).leave_room(sid, namespace, room)
        logger.debug('%s left room %s', sid, room)
        self.__rooms[room] -= 1

        if not self.__rooms[room]:
            del self.__rooms[room]

    def has_clients(self, room):
        clients = self.__rooms.get(room, None)

        if clients:
            return True

        return False



def main(): # pragma: no cover
    get_env('INFRABOX_SERVICE')
    get_env('INFRABOX_VERSION')
    get_env('INFRABOX_DATABASE_HOST')
    get_env('INFRABOX_DATABASE_USER')
    get_env('INFRABOX_DATABASE_PASSWORD')
    get_env('INFRABOX_DATABASE_PORT')
    get_env('INFRABOX_DATABASE_DB')

    get_env('INFRABOX_GITHUB_ENABLED')
    get_env('INFRABOX_GERRIT_ENABLED')
    get_env('INFRABOX_ACCOUNT_SIGNUP_ENABLED')
    get_env('INFRABOX_ACCOUNT_LDAP_ENABLED')
    get_env('INFRABOX_ROOT_URL')

    app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024

    client_manager = ClientManager()
    sio = flask_socketio.SocketIO(app,
                                  path='/api/dashboard/socket.io',
                                  async_mode='eventlet',
                                  client_manager=client_manager)

    @sio.on('connect')
    def __connect():
        try:
            get_token()
        except:
            logger.debug('disconnecting connection')
            return False

        return True

    @sio.on('listen:jobs')
    def __listen_build(project_id):
        logger.debug('listen:jobs for %s', project_id)

        if not project_id:
            logger.debug('project_id not set')
            return flask_socketio.disconnect()

        try:
            uuid.UUID(project_id)
        except:
            logger.debug('project_id not a uuid')
            return flask_socketio.disconnect()

        conn = dbpool.get()
        try:
            p = conn.execute_one_dict('''
                SELECT public
                FROM project
                WHERE id = %s
            ''', [project_id])

            if not p['public']:
                token = get_token()
                if token['type'] == 'user':
                    user_id = token['user']['id']
                    collaborator = is_collaborator(user_id, project_id)

                    if not collaborator:
                        logger.warn('not a collaborator')
                        return flask_socketio.disconnect()
                else:
                    logger.debug('only user token allowed')
                    return flask_socketio.disconnect()

        finally:
            dbpool.put(conn)

        flask_socketio.join_room(project_id)

    @sio.on('listen:console')
    def __listen_console(job_id):
        logger.debug('listen:console for %s', job_id)

        if not job_id:
            logger.debug('job_id not set')
            return flask_socketio.disconnect()

        try:
            uuid.UUID(job_id)
        except:
            logger.debug('job_id not a uuid')
            return flask_socketio.disconnect()

        conn = dbpool.get()
        try:
            u = conn.execute_one_dict('''
                SELECT p.public, j.project_id
                FROM project p
                INNER JOIN job j
                    ON j.project_id = p.id
                    AND j.id = %s
            ''', [job_id])

            if not u:
                logger.warn('job not found')
                return flask_socketio.disconnect()

            if not u['public']:
                token = get_token()
                if token['type'] == 'user':
                    user_id = token['user']['id']
                    collaborator = is_collaborator(user_id, u['project_id'])

                    if not collaborator:
                        logger.warn('not a collaborator')
                        return flask_socketio.disconnect()
                else:
                    logger.debug('only user token allowed')
                    return flask_socketio.disconnect()
        finally:
            dbpool.put(conn)

        flask_socketio.join_room(job_id)

    logger.info('Starting DB listeners')
    sio.start_background_task(dashboard_api.listeners.job.listen, sio)
    sio.start_background_task(dashboard_api.listeners.console.listen, sio, client_manager)

    logger.info('Starting Server')
    sio.run(app, host='0.0.0.0', port=8080)

if __name__ == "__main__": # pragma: no cover
    try:
        main()
    except:
        print_stackdriver()
