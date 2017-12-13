from flask_restplus import Resource

from pyinfraboxutils import get_env, print_stackdriver, get_logger
from pyinfraboxutils.ibrestplus import api, app

import handlers.trigger
import handlers.project

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

    from gevent.wsgi import WSGIServer
    http_server = WSGIServer(('', 8080), app, log=logger)
    http_server.serve_forever()

if __name__ == "__main__": # pragma: no cover
    try:
        main()
    except:
        print_stackdriver()
