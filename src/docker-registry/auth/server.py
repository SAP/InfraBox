from flask import request, g, abort, jsonify

from pyinfraboxutils import get_env, get_logger
from pyinfraboxutils.ibflask import token_required, app

import eventlet
from eventlet import wsgi
eventlet.monkey_patch()

logger = get_logger('docker-registry-auth')

@app.route('/ping')
def ping():
    return jsonify({'status': 200})

@app.route('/v2/') # prevent 301 redirects
@app.route('/v2')
@token_required
def v2():
    token = g.token
    if token['type'] == 'project':
        r = g.db.execute_many('''
            SELECT id FROM auth_token
            WHERE id = %s AND project_id = %s
        ''', (token['id'], token['project']['id'],))

        if len(r) != 1:
            logger.warn('project not found')
            abort(401, 'Unauthorized')

    elif token['type'] == 'job':
        r = g.db.execute_many('''
            SELECT state FROM job
            WHERE id = %s
        ''', (token['job']['id'],))

        if len(r) != 1:
            logger.warn('job not found')
            abort(401, 'Unauthorized')

        state = r[0][0]

        if state not in ('scheduled', 'running'):
            logger.warn('job not running anymore: %s' % token['job']['id'])
            abort(401, 'Unauthorized')
    else: # pragma: no cover
        logger.warn('unsupported token type: %s' % token['type'])
        abort(401, 'Unauthorized')

    return jsonify({'status': 200})

@app.route('/v2/<path:path>/') # prevent 301 redirects
@app.route('/v2/<path:path>')
@token_required
def v2_path(path):
    p = path.split('/')
    method = dict(request.headers).get('X-Original-Method', None)

    if not method:
        logger.warn('no x-original-method header')
        abort(401, 'Unauthorized')

    if len(p) < 2:
        logger.warn('invalid repo')
        abort(401, 'Unauthorized')

    project_id = p[0]
    token = g.token

    if token['type'] == 'project':
        if method != 'GET':
            logger.warn('%s not allowed with project token', request.method)
            abort(401, 'Unauthorized')

        if project_id != token['project']['id']:
            logger.warn('token is not valid for project')
            abort(401, 'Unauthorized')

        r = g.db.execute_many('''
            SELECT * FROM auth_token
            WHERE id = %s AND project_id = %s
        ''', (token['id'], token['project']['id']))

        if len(r) != 1:
            logger.warn('project not found')
            abort(401, 'Unauthorized')
    elif token['type'] == 'job':
        r = g.db.execute_one('''
            SELECT state, project_id FROM job
            WHERE id = %s
        ''', (token['job']['id'],))

        if not r:
            logger.warn('job not found')
            abort(401, 'Unauthorized')

        state = r[0]
        job_project_id = r[1]

        if state not in ('scheduled', 'running'):
            logger.warn('job not running anymore: %s' % token['job']['id'])
            abort(401, 'Unauthorized')

        if project_id != job_project_id:
            logger.warn('job does not belong to project')
            abort(401, 'Unauthorized')

    else: # pragma: no cover
        logger.warn('unsupported token type')
        abort(401, 'Unauthorized')

    return jsonify({'status': 200})

def main(): # pragma: no cover
    get_env('INFRABOX_VERSION')
    get_env('INFRABOX_DATABASE_HOST')
    get_env('INFRABOX_DATABASE_USER')
    get_env('INFRABOX_DATABASE_PASSWORD')
    get_env('INFRABOX_DATABASE_PORT')
    get_env('INFRABOX_DATABASE_DB')

    wsgi.server(eventlet.listen(('0.0.0.0', 8081)), app)

if __name__ == "__main__": # pragma: no cover
    main()
