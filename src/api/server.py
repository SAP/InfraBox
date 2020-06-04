#pylint: disable=unused-import,relative-import,wrong-import-position
import uuid
import os
import sys

import urllib3

import eventlet
eventlet.monkey_patch()

import flask_socketio
import socketio

from flask import request, abort, g, jsonify
from flask_restx import Resource
from requests.exceptions import RequestException

from pyinfraboxutils import get_env, get_logger

from pyinfraboxutils.ibflask import get_token, normalize_token
from pyinfraboxutils.ibrestplus import api, app
from pyinfraboxutils.ibopa import opa_do_auth, opa_start_push_loop
from pyinfraboxutils import dbpool

import handlers
import settings
import internal

import listeners.console
import listeners.job


logger = get_logger('api')

@app.route('/ping')
@app.route('/api/ping')
def ping():
    return jsonify({'status': 200})

@app.route('/api/status')
def status():
    cluster_name = get_env("INFRABOX_CLUSTER_NAME")
    status = g.db.execute_one_dict("""
                SELECT active, enabled
                FROM cluster
                WHERE name = %s
            """, [cluster_name])
    if not status['active'] or not status['enabled']:
        return jsonify(status), 503
    return jsonify({'status': "active"})

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

    urllib3.disable_warnings()

    @sio.on('listen:jobs')
    def __listen_jobs(project_id):
        logger.debug('listen:jobs for %s', project_id)

        if not project_id:
            logger.debug('project_id not set')
            return flask_socketio.disconnect()

        if not sio_is_authorized(["listen:jobs", project_id]):
            return flask_socketio.disconnect()

        flask_socketio.join_room(project_id)

    @sio.on('listen:build')
    def __listen_build(build_id):
        logger.debug('listen:build for %s', build_id)

        if not build_id:
            logger.debug('build_id not set')
            return flask_socketio.disconnect()

        try:
            uuid.UUID(build_id)
        except:
            logger.debug('build_id not a uuid')
            return flask_socketio.disconnect()

        if not sio_is_authorized(['listen:build', build_id]):
            return flask_socketio.disconnect()

        conn = dbpool.get()
        try:
            token = normalize_token(get_token())

            project_id = token['project']['id']

            build = conn.execute_one('''
                SELECT id
                FROM build
                WHERE project_id = %s AND id = %s
            ''', [project_id, build_id])

            if not build:
                logger.debug('build does not belong to project')
                return flask_socketio.disconnect()
        except:
            logger.exception("Exception occured")
            return flask_socketio.disconnect()
        finally:
            dbpool.put(conn)

        flask_socketio.join_room(build_id)

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

        if not sio_is_authorized(['listen:console', job_id]):
            return flask_socketio.disconnect()

        token = normalize_token(get_token())
        conn = dbpool.get()
        try:
            project_id = token['project']['id']

            build = conn.execute_one('''
                SELECT id
                FROM job
                WHERE project_id = %s AND id = %s
            ''', [project_id, job_id])

            if not build:
                logger.debug('job does not belong to project')
                return flask_socketio.disconnect()
        except:
            logger.exception("Exception occured")
            return flask_socketio.disconnect()
        finally:
            dbpool.put(conn)

        flask_socketio.join_room(job_id)

    @sio.on('listen:dashboard-console')
    def __listen_dashboard_console(job_id):
        logger.debug('listen:dashboard-console for %s', job_id)

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

            if not sio_is_authorized(['listen:dashboard-console', u['project_id'], job_id]):
                return flask_socketio.disconnect()

        except:
            logger.exception("Exception occured")
            return flask_socketio.disconnect()
        finally:
            dbpool.put(conn)

        flask_socketio.join_room(job_id)

    def sio_is_authorized(path):
        g.db = dbpool.get()
        try:
            # Assemble Input Data for Open Policy Agent
            opa_input = {
                "input": {
                    "method": "WS",
                    "path": path,
                    "token": normalize_token(get_token())
                }
            }

            authorized = opa_do_auth(opa_input)
            if not authorized:
                logger.warn("Unauthorized socket.io access attempt")
                return False
            return True
        except RequestException as e:
            logger.error(e)
            return False
        finally:
            dbpool.put(g.db)
            g.db = None


    logger.info('Starting DB listeners')
    sio.start_background_task(listeners.job.listen, sio)
    sio.start_background_task(listeners.console.listen, sio, client_manager)

    logger.info('Starting repeated push of data to Open Policy Agent')
    opa_start_push_loop()


    port = int(os.environ.get('INFRABOX_PORT', 8080))
    logger.info('Starting Server on port %s', port)
    sio.run(app, host='0.0.0.0', port=port)

if __name__ == "__main__": # pragma: no cover
    main()
