import base64
from uuid import UUID

from bottle import get, request, run, response, install

from pyinfraboxutils import get_env, print_stackdriver
from pyinfraboxutils.ibbottle import InfraBoxPostgresPlugin
from pyinfraboxutils.db import connect_db

def validate_uuid4(uuid_string):
    try:
        val = UUID(uuid_string, version=4)
    except ValueError:
        return False

    return val.hex == uuid_string.replace('-', '')

def auth_project(project_id, conn):
    if request.method != 'GET':
        response.status = 401
        return "UNAUTHORIZED"

    auth = dict(request.headers).get('Authorization', None)

    if not auth:
        response.status = 401
        return "UNAUTHORIZED"

    if not auth.startswith("Basic "):
        response.status = 401
        return "UNAUTHORIZED"

    auth = auth.split(" ")[1]

    decoded = base64.b64decode(auth)
    s = decoded.split('infrabox:')

    if len(s) != 2:
        response.status = 401
        return "UNAUTHORIZED"

    token = s[1]

    if not validate_uuid4(token) or not validate_uuid4(project_id):
        response.status = 401
        return "BAD REQUEST"

    cur = conn.cursor()
    cur.execute('''SELECT * FROM auth_token WHERE project_id = %s AND token = %s''', (project_id, token))
    r = cur.fetchall()

    if len(r) == 1:
        return "OK"

    response.status = 401
    return "UNAUTHORIZED"


@get('/v2/') # prevent 301 redirects
@get('/v2')
def v2(conn):
    auth = dict(request.headers).get('Authorization', None)

    if not auth:
        response.status = 401
        return "UNAUTHORIZED"

    if not auth.startswith("Basic "):
        response.status = 401
        return "UNAUTHORIZED"

    auth = auth.split(" ")[1]

    decoded = base64.b64decode(auth)
    s = decoded.split(':')

    if len(s) != 2:
        response.status = 401
        return "UNAUTHORIZED"

    token = s[1]

    if not validate_uuid4(token):
        response.status = 401
        return "BAD REQUEST"

    cur = conn.cursor()
    cur.execute('SELECT * FROM auth_token WHERE token = %s', (token, ))
    r = cur.fetchall()

    if len(r) == 1:
        response.status = 200
        return "OK"

    response.status = 401
    return "UNAUTHORIZED"

@get('/v2/<path:path>/') # prevent 301 redirects
@get('/v2/<path:path>')
def v2_project_tags_list(path, conn):
    if dict(request.headers)['X-Original-Method'] != 'GET':
        response.status = 401
        return "UNAUTHORIZED"

    p = path.split('/')

    if len(p) < 3:
        response.status = 401
        return "UNAUTHORIZED"

    if p[2] not in ('manifests', 'blobs'):
        response.status = 401
        return "UNAUTHORIZED"

    project_id = p[0]
    return auth_project(project_id, conn)

@get('/ping')
def ping():
    return "OK"

def main():
    get_env('INFRABOX_SERVICE')
    get_env('INFRABOX_VERSION')
    get_env('INFRABOX_DATABASE_HOST')
    get_env('INFRABOX_DATABASE_USER')
    get_env('INFRABOX_DATABASE_PASSWORD')
    get_env('INFRABOX_DATABASE_PORT')
    get_env('INFRABOX_DATABASE_DB')

    connect_db() # Wait until db is ready

    install(InfraBoxPostgresPlugin())
    run(host='0.0.0.0', port=8081)

if __name__ == "__main__":
    try:
        main()
    except:
        print_stackdriver()
