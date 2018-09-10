#pylint: disable=unused-import,relative-import,wrong-import-position
import uuid
import os
import sys

import eventlet
eventlet.monkey_patch()

import flask_socketio
import socketio

from flask import request, abort, g, jsonify
from flask_restplus import Resource

from pyinfraboxutils import get_env, get_logger

from pyinfraboxutils.ibflask import require_token, is_collaborator
from pyinfraboxutils.ibrestplus import api, app
from pyinfraboxutils import dbpool

import handlers
import settings

import listeners.console
import listeners.job

logger = get_logger('api')

@app.route('/ping')
def ping():
    return jsonify({'status': 200})

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
    get_env('INFRABOX_VERSION')
    get_env('INFRABOX_DATABASE_HOST')
    get_env('INFRABOX_DATABASE_USER')
    get_env('INFRABOX_DATABASE_PASSWORD')
    get_env('INFRABOX_DATABASE_PORT')
    get_env('INFRABOX_DATABASE_DB')

    get_env('INFRABOX_GENERAL_REPORT_ISSUE_URL')

    if get_env('INFRABOX_STORAGE_GCS_ENABLED') == 'true':
        get_env('GOOGLE_APPLICATION_CREDENTIALS')
        get_env('INFRABOX_STORAGE_GCS_BUCKET')

    if get_env('INFRABOX_STORAGE_S3_ENABLED') == 'true':
        get_env('INFRABOX_STORAGE_S3_BUCKET')
        get_env('INFRABOX_STORAGE_S3_REGION')

    app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024 * 4
    client_manager = ClientManager()
    sio = flask_socketio.SocketIO(app,
                                  path='/api/v1/socket.io',
                                  async_mode='eventlet',
                                  client_manager=client_manager)

    @sio.on('listen:jobs')
    def __listen_jobs(project_id):
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
                token = require_token()
                if token['type'] == 'user':
                    user_id = token['user']['id']
                    collaborator = is_collaborator(user_id, project_id, db=conn)

                    if not collaborator:
                        logger.warn('not a collaborator')
                        return flask_socketio.disconnect()
                else:
                    logger.debug('only user token allowed')
                    return flask_socketio.disconnect()

        finally:
            dbpool.put(conn)

        flask_socketio.join_room(project_id)

    @sio.on('listen:build')
    def __listen_build(build_id):
        logger.debug('listen:build for %s', build_id)
        token = require_token()

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
        token = require_token()

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

    @sio.on('listen:dashboard-console')
    def __listen_dashboard_console(job_id):
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
                token = require_token()
                if token['type'] == 'user':
                    user_id = token['user']['id']
                    collaborator = is_collaborator(user_id, u['project_id'], db=conn)

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
    sio.start_background_task(listeners.job.listen, sio)
    sio.start_background_task(listeners.console.listen, sio, client_manager)

    port = int(os.environ.get('INFRABOX_PORT', 8080))
    logger.info('Starting Server on port %s', port)
    sio.run(app, host='0.0.0.0', port=port)

if __name__ == "__main__": # pragma: no cover
    main()
