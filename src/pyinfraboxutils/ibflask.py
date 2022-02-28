import base64

from functools import wraps

import requests

from flask import Flask, g, jsonify, request, abort

from pyinfrabox.utils import validate_uuid

from pyinfraboxutils import get_logger, get_env, dbpool
from pyinfraboxutils.db import DB, connect_db
from pyinfraboxutils.token import decode

app = Flask(__name__)
app.url_map.strict_slashes = False

logger = get_logger('ibflask')

@app.before_request
def before_request():
    def release_db():
        db = getattr(g, 'db', None)
        if not db:
            return

        dbpool.put(db)
        g.db = None

    g.release_db = release_db

    g.db = dbpool.get()

    if app.config['OPA_ENABLED']:
        g.token = normalize_token(get_token())
        check_request_authorization()

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

def get_token():
    auth = dict(request.headers).get('Authorization', None)
    cookie = request.cookies.get('token', None)

    if auth:
        if auth.startswith("Basic "):
            auth = auth.split(" ")[1]

            try:
                decoded = base64.b64decode(auth)
            except:
                logger.warn('could not base64 decode auth header %s', auth)
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
        elif auth.startswith("token ") or auth.startswith("bearer ") or auth.startswith("Bearer "):
            token = auth.split(" ")[1]

            try:
                token = decode(token.encode('utf8'))
            except Exception as e:
                logger.exception(e)
                return None

            return token
        else:
            logger.debug('Invalid auth header format')
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
        return None

def check_request_authorization():
    try:
        # Assemble Input Data for Open Policy Agent
        opa_input = {
            "input": {
                "method": request.method,
                "path": get_path_array(request.path),
                "token": g.token,
            }
        }

        original_method = dict(request.headers).get('X-Original-Method', None)
        if original_method is not None:
            opa_input["input"]["original_method"] = original_method

        from pyinfraboxutils.ibopa import opa_do_auth
        is_authorized = opa_do_auth(opa_input)

        if not is_authorized:
            logger.info("Rejected unauthorized request")
            abort(401, 'Unauthorized')

    except requests.exceptions.RequestException as e:
        logger.error(e)
        abort(500, 'Authorization failed')

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

def normalize_token(token):
    # Enrich job token
    if token is None or not "type" in token:
        return token
    if token["type"] == "job":
        try:
            return enrich_job_token(token)
        except:
            logger.exception("Enrichment of job token failed")
            return None
    # Legacy
    if token["type"] == "project-token":
        token["type"] = 'project'

    # Validate user token
    if token["type"] == "user":
        return validate_user_token(token)

    # Validate project_token
    elif token["type"] == "project":
        if not validate_project_token(token):
            return None

    return token

def enrich_job_token(token):
    if not ("job" in token and "id" in token["job"] and validate_uuid(token["job"]["id"])):
        raise LookupError('invalid job id')

    job_id = token["job"]["id"]

    r = g.db.execute_one('''
        SELECT state, project_id, name
        FROM job
        WHERE id = %s''', [job_id])

    if not r:
        raise LookupError('job not found')


    token['job']['state'] = r[0]
    token['job']['name'] = r[2]
    token['project'] = {}
    token['project']['id'] = r[1]
    return token

def validate_user_token(token):
    if not ("user" in token and "id" in token["user"] and validate_uuid(token['user']['id'])):
        return None

    u = g.db.execute_one('''
        SELECT id, role FROM "user" WHERE id = %s
    ''', [token['user']['id']])
    if not u:
        logger.warn('user not found')
        return None
    token['user']['role'] = u[1]
    return token

def validate_project_token(token):
    if not ("project" in token and "id" in token['project'] and validate_uuid(token['project']['id'])
            and "id" in token and validate_uuid(token['id'])):
        return False

    r = g.db.execute_one('''
        SELECT id FROM auth_token
        WHERE id = %s AND project_id = %s
    ''', (token['id'], token['project']['id'],))
    if not r:
        logger.warn('project token not valid')
        return False
    return True

def get_path_array(path):
    pathstring = path.strip()
    if pathstring[-1] == "/":
        pathstring = pathstring[:-1]
    return pathstring.split("/")[1:]
