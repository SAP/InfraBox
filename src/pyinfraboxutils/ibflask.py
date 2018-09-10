import base64
import requests
import os
import json

from functools import wraps

from flask import Flask, g, jsonify, request, abort

from pyinfraboxutils import get_logger
from pyinfraboxutils.db import DB, connect_db
from pyinfraboxutils.token import decode

app = Flask(__name__)
app.url_map.strict_slashes = False

logger = get_logger('ibflask')

def get_token():
    auth = dict(request.headers).get('Authorization', None)
    cookie = request.cookies.get('token', None)

    if auth:
        if auth.startswith("Basic "):
            auth = auth.split(" ")[1]

            try:
                decoded = base64.b64decode(auth)
            except:
                logger.warn('could not base64 decode auth header')
                return None

            s = decoded.split('infrabox:')

            if len(s) != 2:
                logger.warn('Invalid auth header format')
                return None

            try:
                token = decode(s[1])
            except Exception as e:
                logger.exception(e)
                return None

            return token
        elif auth.startswith("token ") or auth.startswith("bearer "):
            token = auth.split(" ")[1]

            try:
                token = decode(token.encode('utf8'))
            except Exception as e:
                logger.exception(e)
                return None

            return token
        else:
            logger.warn('Invalid auth header format')
            return None
    elif cookie:
        token = cookie
        try:
            token = decode(token.encode('utf8'))
        except Exception as e:
            logger.exception(e)
            return None

        return token
    else:
        logger.info('No auth header')
        return None

def require_token():
    token = get_token()
    if token == None:
        abort(401, 'Unauthorized')
    return token

try:
    #pylint: disable=ungrouped-imports,wrong-import-position
    from pyinfraboxutils import dbpool
    logger.info('Using DB Pool')

    @app.before_request
    def before_request():
        g.db = dbpool.get()

        input = json.dumps({
            "method": request.method,
            "path": request.path.strip().split("/")[1:]
        #    "token": require_token()
        })
            
        rsp = requests.post(os.environ['INFRABOX_OPA_HOST']+"/v1/data/httpapi/authz", data=input)
        rspp = rsp

        def release_db():
            db = getattr(g, 'db', None)
            if not db:
                return

            dbpool.put(db)
            g.db = None

        g.release_db = release_db

except:
    @app.before_request
    def before_request():
        g.db = DB(connect_db())

        input = jsonify({
            "method": request.method,
            "path": request.path.strip().split("/")[1:]
        #    "token": require_token()
        })
        print(input)

        def release_db():
            db = getattr(g, 'db', None)
            if not db:
                return

            db.close()
            g.db = None

        g.release_db = release_db

@app.teardown_request
def teardown_request(_):
    try:
        release_db = getattr(g, 'release_db', None)
        if release_db:
            release_db()
    except Exception as e:
        logger.error(_)
        logger.exception(e)


@app.errorhandler(404)
def not_found(error):
    msg = error.description

    if not msg:
        msg = 'Not Found'

    return jsonify({'message': msg, 'status': 404}), 404

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({'message': error.description, 'status': 401}), 401

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'message': error.description, 'status': 400}), 400

def OK(message, data=None):
    d = {'message': message, 'status': 200}

    if data:
        d['data'] = data

    return jsonify(d)

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g.token = require_token()
        return f(*args, **kwargs)

    return decorated_function

def check_job_belongs_to_project(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        project_id = kwargs.get('project_id')
        job_id = kwargs.get('job_id')

        assert project_id
        assert job_id

        r = g.db.execute_one('''
            SELECT id
            FROM job
            WHERE id = %s AND project_id = %s
        ''', [job_id, project_id])

        if not r:
            logger.debug('job does not belong to project')
            abort(404)

        return f(*args, **kwargs)
    return decorated_function

def job_token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = require_token()

        if token['type'] != 'job':
            logger.warn('token type is not job but "%s"', token['type'])
            abort(401, 'Unauthorized')

        job_id = token['job']['id']
        r = g.db.execute_one('''
            SELECT state, project_id, name
            FROM job
            WHERE id = %s''', [job_id])

        if not r:
            logger.warn('job not found')
            abort(401, 'Unauthorized')

        job_state = r[0]
        if job_state not in ('queued', 'running', 'scheduled'):
            abort(401, 'Unauthorized')


        token['job']['state'] = r[0]
        token['job']['name'] = r[2]
        token['project'] = {}
        token['project']['id'] = r[1]
        g.token = token

        return f(*args, **kwargs)

    return decorated_function

def validate_job_token(token):
    job_id = token['job']['id']
    r = g.db.execute_one('''
        SELECT state, project_id, name
        FROM job
        WHERE id = %s''', [job_id])

    if not r:
        logger.warn('job not found')
        abort(401, 'Unauthorized')

    job_state = r[0]
    if job_state not in ('queued', 'running', 'scheduled'):
        abort(401, 'Unauthorized')


    token['job']['state'] = r[0]
    token['job']['name'] = r[2]
    token['project'] = {}
    token['project']['id'] = r[1]
    g.token = token

def is_collaborator(user_id, project_id, db=None):
    if not db:
        db = g.db

    u = db.execute_many('''
        SELECT co.*
        FROM collaborator co
        INNER JOIN "user" u
            ON u.id = co.user_id
            AND u.id = %s
            AND co.project_id = %s
    ''', [user_id, project_id])

    return u

def is_public(project_id, project_name):
    if project_id:
        p = g.db.execute_one_dict('''
            SELECT public
            FROM project
            WHERE id = %s
        ''', [project_id])

        if not p:
            abort(404, 'Project not found')

        if p['public']:
            return True
    elif project_name:
        p = g.db.execute_one_dict('''
            SELECT public
            FROM project
            WHERE name = %s
        ''', [project_name])

        if not p:
            abort(404, 'Project not found')

        if p['public']:
            return True
    else:
        logger.warn('no project_id or project_name')
        abort(401, 'Unauthorized')

    return False


def validate_user_token(token, check_project_access, project_id, check_project_owner):
    u = g.db.execute_one('''
        SELECT id FROM "user" WHERE id = %s
    ''', [token['user']['id']])

    if not u:
        logger.warn('user not found')
        abort(401, 'Unauthorized')

    if check_project_access:
        if not project_id:
            logger.warn('no project id')
            abort(401, 'Unauthorized')

        u = is_collaborator(token['user']['id'], project_id)

        if not u:
            logger.warn('user has no access to project')
            abort(401, 'Unauthorized')

    if check_project_owner:
        if not project_id:
            logger.warn('no project id')
            abort(401, 'Unauthorized')

        u = g.db.execute_many('''
            SELECT co.*
            FROM collaborator co
            INNER JOIN "user" u
                ON u.id = co.user_id
                AND u.id = %s
                AND co.project_id = %s
                AND co.owner = true
        ''', [token['user']['id'], project_id])

        if not u:
            logger.warn('user has no access to project')
            abort(401, 'Unauthorized')

def validate_project_token(token, check_project_access, project_id):
    if not check_project_access:
        return

    if project_id != token['project']['id']:
        logger.warn('token not valid for project')
        abort(401, 'Unauthorized')

def auth_required(types,
                  check_project_access=True,
                  check_project_owner=False,
                  check_admin=False,
                  allow_if_public=False):
    def actual_decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            project_id = kwargs.get('project_id', None)
            project_name = kwargs.get('project_name', None)

            if allow_if_public:
                if is_public(project_id, project_name):
                    return f(*args, **kwargs)

            token = require_token()
            token_type = token['type']
            g.token = token

            if token_type == 'project-token':
                token_type = 'project'

            if token_type not in types:
                logger.warn('token type "%s" not allowed here', token_type)
                abort(401, 'Unauthorized')

            if token_type == 'job':
                if check_project_owner:
                    logger.warn('Project owner validation not possible with job token')
                    abort(401, 'Unauthorized')

                validate_job_token(token)
            elif token_type == 'user':
                if token['user']['id'] != '00000000-0000-0000-0000-000000000000':
                    if check_admin:
                        abort(401, 'Unauthorized')
                    else:
                        validate_user_token(token,
                                            check_project_access,
                                            project_id,
                                            check_project_owner)
            elif token_type == 'project':
                project_id = kwargs.get('project_id')

                if check_project_owner:
                    logger.warn('Project owner validation not possible with project token')
                    abort(401, 'Unauthorized')

                validate_project_token(token, check_project_access, project_id)
            else:
                logger.warn('unhandled token type')
                abort(401, 'Unauthorized')

            return f(*args, **kwargs)

        return decorated_function
    return actual_decorator