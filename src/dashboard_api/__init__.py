import eventlet
eventlet.monkey_patch()

import flask_socketio

from flask import jsonify

from pyinfraboxutils import get_env, print_stackdriver, get_logger
from pyinfraboxutils.ibrestplus import app, api

import dashboard_api.handlers

logger = get_logger('dashboard-api')

project_ns = api.namespace('api/dashboard/projects/',
                           description='Project related operations')


@app.route('/ping')
def ping():
    return jsonify({'status': 200})

def main(): # pragma: no cover
    get_env('INFRABOX_SERVICE')
    get_env('INFRABOX_VERSION')
    get_env('INFRABOX_DATABASE_HOST')
    get_env('INFRABOX_DATABASE_USER')
    get_env('INFRABOX_DATABASE_PASSWORD')
    get_env('INFRABOX_DATABASE_PORT')
    get_env('INFRABOX_DATABASE_DB')

    app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024

    sio = flask_socketio.SocketIO(app,
                                  path='/dashboard/socket.io',
                                  async_mode='eventlet')

    logger.info('Starting DB listeners')

    logger.info('Starting Server')
    sio.run(app, host='0.0.0.0', port=8080)

if __name__ == "__main__": # pragma: no cover
    try:
        main()
    except:
        print_stackdriver()
