import base64
from functools import wraps

from pyinfraboxutils import get_logger
from pyinfraboxutils.db import DB, connect_db
from pyinfraboxutils.token import decode

from flask import Flask, g, jsonify, request, abort
app = Flask(__name__)

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
                abort(401, 'Unauthorized')

            s = decoded.split('infrabox:')

            if len(s) != 2:
                logger.warn('Invalid auth header format')
                abort(401, 'Unauthorized')

            try:
                token = decode(s[1])
            except Exception as e:
                logger.exception(e)
                abort(401, 'Unauthorized')

            return token
        elif auth.startswith("token "):
            token = auth.split(" ")[1]

            try:
                token = decode(token.encode('utf8'))
            except Exception as e:
                logger.exception(e)
                abort(401, 'Unauthorized')

            return token
        else:
            logger.warn('Invalid auth header format')
            abort(401, 'Unauthorized')
    elif cookie:
        token = cookie
        try:
            token = decode(token.encode('utf8'))
        except Exception as e:
            logger.exception(e)
            abort(401, 'Unauthorized')

        return token
    else:
        logger.warn('No auth header')
        abort(401, 'Unauthorized')

try:
    #pylint: disable=ungrouped-imports
    from pyinfraboxutils import dbpool
    logger.info('Using DB Pool')

    @app.before_request
    def before_request():
        g.db = dbpool.get()

    @app.teardown_request
    def teardown_request(_):
        db = getattr(g, 'db', None)
        if db is not None:
            dbpool.put(db)

except:
    @app.before_request
    def before_request():
        g.db = DB(connect_db())

    @app.teardown_request
    def teardown_request(_):
        db = getattr(g, 'db', None)
        if db is not None:
            db.close()

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
        g.token = get_token()
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
        token = get_token()

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
            logger.warn('job not in an active state')
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
        logger.warn('job not in an active state')
        abort(401, 'Unauthorized')


    token['job']['state'] = r[0]
    token['job']['name'] = r[2]
    token['project'] = {}
    token['project']['id'] = r[1]
    g.token = token


def validate_user_token(token, check_project_access, project_id):
    g.token = token

    u = g.db.execute_one('''
        SELECT id FROM "user" WHERE id = %s
    ''', [token['user']['id']])

    if not u:
        logger.warn('user not found')
        abort(401, 'Unauthorized')

    if not check_project_access:
        return

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

def auth_token_required(types, check_project_access=True):
    def actual_decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = get_token()
            token_type = token['type']

            if token_type == 'project-token':
                token_type = 'project'

            if token_type not in types:
                logger.warn('token type "%s" not allowed here', token_type)
                abort(401, 'Unauthorized')

            if token_type == 'job':
                validate_job_token(token)
            elif token_type == 'user':
                project_id = kwargs.get('project_id')
                validate_user_token(token, check_project_access, project_id)
            elif token_type == 'project':
                project_id = kwargs.get('project_id')
                validate_project_token(token, check_project_access, project_id)
            else:
                logger.warn('unhandled token type')
                abort(401, 'Unauthorized')

            return f(*args, **kwargs)

        return decorated_function
    return actual_decorator
