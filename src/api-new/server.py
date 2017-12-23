#pylint: disable=unused-import,relative-import,wrong-import-position
import uuid

import eventlet
eventlet.monkey_patch()

import flask_socketio
import socketio

from flask import request, abort, g
from flask_restplus import Resource
from werkzeug.debug import DebuggedApplication

from pyinfraboxutils import get_env, print_stackdriver, get_logger
from pyinfraboxutils.ibrestplus import api, app
from pyinfraboxutils.ibflask import get_token
from pyinfraboxutils import dbpool

import handlers.project
import handlers.trigger
import handlers.job

import listeners.console
import listeners.job

logger = get_logger('api')
ns = api.namespace('ping', description='Health checks')

@ns.route('/')
class Ping(Resource):
    def get(self):
        return {'status': 200}

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

    app.config['MAX_CONTENT_LENGTH'] = 128 * 1024 * 1024
    client_manager = ClientManager()
    sio = flask_socketio.SocketIO(app,
                                  path='/api/v1/socket.io',
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

    @sio.on('listen:build')
    def __listen_build(build_id):
        logger.debug('listen:build for %s', build_id)
        token = get_token()

        if not build_id:
            logger.debug('build_id not set')
            return flask_socketio.disconnect()

        try:
            uuid.UUID(build_id)
        except:
            logger.debug('build_id not a uuid')
            return flask_socketio.disconnect()

        conn = dbpool.get()
        try:
            if token['type'] not in ('project', 'project-token'):
                logger.debug('only project token allowed')
                return flask_socketio.disconnect()

            project_id = token['project']['id']

            build = conn.execute_one('''
                SELECT id
                FROM build
                WHERE project_id = %s AND id = %s
            ''', [project_id, build_id])

            if not build:
                logger.debug('build does not belong to project')
                return flask_socketio.disconnect()
        finally:
            dbpool.put(conn)

        flask_socketio.join_room(build_id)

    @sio.on('listen:console')
    def __listen_console(job_id):
        logger.debug('listen:console for %s', job_id)
        token = get_token()

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
            if token['type'] not in ('project', 'project-token'):
                logger.debug('only project token allowed')
                return flask_socketio.disconnect()

            project_id = token['project']['id']

            build = conn.execute_one('''
                SELECT id
                FROM job
                WHERE project_id = %s AND id = %s
            ''', [project_id, job_id])

            if not build:
                logger.debug('job does not belong to project')
                return flask_socketio.disconnect()
        finally:
            dbpool.put(conn)

        flask_socketio.join_room(job_id)

    logger.info('Starting DB listeners')
    sio.start_background_task(listeners.job.listen, sio)
    sio.start_background_task(listeners.console.listen, sio, client_manager)

    logger.info('Starting Server')
    sio.run(app, host='0.0.0.0', port=8080)

if __name__ == "__main__": # pragma: no cover
    try:
        main()
    except:
        print_stackdriver()
