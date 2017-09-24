import os
import traceback
import base64
import json
from uuid import UUID
import logging

from flask import Flask, request
import psycopg2
import psycopg2.extensions

app = Flask(__name__)

log = logging.getLogger('werkzeug')

conn = psycopg2.connect(dbname=os.environ['INFRABOX_DATABASE_DB'],
                        user=os.environ['INFRABOX_DATABASE_USER'],
                        password=os.environ['INFRABOX_DATABASE_PASSWORD'],
                        host=os.environ['INFRABOX_DATABASE_HOST'],
                        port=os.environ['INFRABOX_DATABASE_PORT'])

conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

def validate_uuid4(uuid_string):
    try:
        val = UUID(uuid_string, version=4)
    except ValueError:
        return False

    return val.hex == uuid_string.replace('-', '')

def auth_project(project_id):
    if request.method != 'GET':
        return "UNAUTHORIZED", 401

    auth = request.headers.get('authorization', None)

    if not auth:
        return "UNAUTHORIZED", 401

    if not auth.startswith("Basic "):
        return "UNAUTHORIZED", 401

    auth = auth.split(" ")[1]

    decoded = base64.b64decode(auth)
    s = decoded.split('infrabox:')

    if len(s) != 2:
        return "UNAUTHORIZED", 401

    token = s[1]

    if not validate_uuid4(token) or not validate_uuid4(project_id):
        return "BAD REQUEST", 401

    cur = conn.cursor()
    cur.execute('''SELECT * FROM auth_token WHERE project_id = %s AND token = %s''', (project_id, token))
    r = cur.fetchall()

    if len(r) == 1:
        return "OK", 200

    return "UNAUTHORIZED", 401


@app.route('/v2/') # prevent 301 redirects
@app.route('/v2')
def v2():
    auth = request.headers.get('authorization', None)

    if not auth:
        return "UNAUTHORIZED", 401

    if not auth.startswith("Basic "):
        return "UNAUTHORIZED", 401

    auth = auth.split(" ")[1]

    decoded = base64.b64decode(auth)
    s = decoded.split(':')

    if len(s) != 2:
        return "UNAUTHORIZED", 401

    token = s[1]

    if not validate_uuid4(token):
        return "BAD REQUEST", 401

    cur = conn.cursor()
    cur.execute('SELECT * FROM auth_token WHERE token = %s', (token, ))
    r = cur.fetchall()

    if len(r) == 1:
        return "OK", 200

    return "UNAUTHORIZED", 401

@app.route('/v2/<path:path>/') # prevent 301 redirects
@app.route('/v2/<path:path>')
def v2_project_tags_list(path):
    if request.headers['X-Original-Method'] != 'GET':
        return "UNAUTHORIZED", 401

    p = path.split('/')

    if len(p) < 3:
        return "UNAUTHORIZED", 401

    if p[2] not in ('manifests', 'blobs'):
        return "UNAUTHORIZED", 401

    project_id = p[0]
    return auth_project(project_id)

@app.route('/ping')
def ping():
    return "OK", 200

def main():
    if 'INFRABOX_SERVICE' not in os.environ:
        raise Exception("INFRABOX_SERVICE not set")

    if 'INFRABOX_VERSION' not in os.environ:
        raise Exception("INFRABOX_VERSION not set")

    if "INFRABOX_DATABASE_HOST" not in os.environ:
        raise Exception("INFRABOX_DATABASE_HOST not set")

    if "INFRABOX_DATABASE_USER" not in os.environ:
        raise Exception("INFRABOX_DATABASE_USER not set")

    if "INFRABOX_DATABASE_PASSWORD" not in os.environ:
        raise Exception("INFRABOX_DATABASE_PASSWORD not set")

    app.run(host='0.0.0.0', port=80)

def print_stackdriver():
    print json.dumps({
        "serviceContext": {
            "service": os.environ.get('INFRABOX_SERVICE', 'unknown'),
            "version": os.environ.get('INFRABOX_VERSION', 'unknown')
        },
        "message": traceback.format_exc(),
        "severity": 'ERROR'
    })

@app.errorhandler(Exception)
def all_exception_handler(error):
    app.logger.error(error)
    return 'Error', 500

if __name__ == "__main__":
    try:
        main()
    except:
        print_stackdriver()
