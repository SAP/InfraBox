from flask import jsonify

from pyinfraboxutils import get_env, get_logger
from pyinfraboxutils.ibflask import app
from pyinfraboxutils.ibopa import opa_push_all

logger = get_logger('docker-registry-auth')

@app.route('/ping')
def ping():
    return jsonify({'status': 200})

@app.route('/v2/') # prevent 301 redirects
@app.route('/v2')
def v2():
    # Authorization in src/opa/policies/docker-registry-auth.rego
    return jsonify({'status': 200})

@app.route('/v2/<path:path>/') # prevent 301 redirects
@app.route('/v2/<path:path>')
def v2_path(path):
    # Authorization in src/opa/policies/docker-registry-auth.rego

    return jsonify({'status': 200})

def main(): # pragma: no cover
    get_env('INFRABOX_VERSION')
    get_env('INFRABOX_DATABASE_HOST')
    get_env('INFRABOX_DATABASE_USER')
    get_env('INFRABOX_DATABASE_PASSWORD')
    get_env('INFRABOX_DATABASE_PORT')
    get_env('INFRABOX_DATABASE_DB')
    get_env('INFRABOX_OPA_HOST')
    get_env('INFRABOX_OPA_PORT')

    from gevent.wsgi import WSGIServer
    http_server = WSGIServer(('', 8081), app, log=logger)
    http_server.serve_forever()

if __name__ == "__main__": # pragma: no cover
    main()
