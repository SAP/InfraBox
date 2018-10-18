import eventlet
from eventlet import wsgi
eventlet.monkey_patch()

from flask import jsonify

from pyinfraboxutils import get_env, get_logger
from pyinfraboxutils.ibflask import app
from pyinfraboxutils.db import DB, connect_db
from pyinfraboxutils.ibopa import opa_start_push_loop

import psycopg2
import psycopg2.extensions

logger = get_logger('docker-registry-auth')

app.config['OPA_ENABLED'] = True

@app.route('/ping')
def ping():
    return jsonify({'status': 200})

@app.route('/v2/') # prevent 301 redirects
@app.route('/v2')
def v2():
    # Authorization in src/openpolicyagent/policies/docker-registry-auth.rego
    return jsonify({'status': 200})

@app.route('/v2/<path:path>/') # prevent 301 redirects
@app.route('/v2/<path:path>')
def v2_path(path):
    # Authorization in src/openpolicyagent/policies/docker-registry-auth.rego

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
    get_env('INFRABOX_OPA_PUSH_INTERVAL')

    conn = connect_db()

    opa_start_push_loop()
    wsgi.server(eventlet.listen(('0.0.0.0', 8081)), app)

if __name__ == "__main__": # pragma: no cover
    main()
