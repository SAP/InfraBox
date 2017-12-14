#pylint: disable=unused-import,relative-import
from flask import request
from flask_restplus import Resource
from flask_socketio import SocketIO
from werkzeug.debug import DebuggedApplication

from pyinfraboxutils import get_env, print_stackdriver, get_logger
from pyinfraboxutils.ibrestplus import api, app
from pyinfraboxutils.ibflask import auth_token_required

import handlers.trigger
import handlers.project
import handlers.upload

logger = get_logger('api')
ns = api.namespace('ping', description='Health checks')

@ns.route('/')
class Ping(Resource):
    def get(self):
        return {'status': 200}

def main(): # pragma: no cover
    get_env('INFRABOX_SERVICE')
    get_env('INFRABOX_VERSION')
    get_env('INFRABOX_DATABASE_HOST')
    get_env('INFRABOX_DATABASE_USER')
    get_env('INFRABOX_DATABASE_PASSWORD')
    get_env('INFRABOX_DATABASE_PORT')
    get_env('INFRABOX_DATABASE_DB')

    app.config['MAX_CONTENT_LENGTH'] = 128 * 1024 * 1024
    socketio = SocketIO(app, path='/api/v1/socket.io')

    @socketio.on('listen:build')
    @auth_token_required(['project'], check_project_access=False)
    def listen_build(build_id):
        # TODO: check project access
        if not build_id:
            abort(400, 'no build id')


    socketio.run(app, port=8080, debug=True)


    #from gevent.wsgi import WSGIServer
    #http_server = WSGIServer(('', 8080), DebuggedApplication(app), log=logger)
    #http_server.serve_forever()

if __name__ == "__main__": # pragma: no cover
    try:
        main()
    except:
        print_stackdriver()
