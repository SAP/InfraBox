import uuid
from datetime import datetime

from flask import g, request
from flask_restx import Resource, fields
from pyinfraboxutils.ibflask import OK
from pyinfraboxutils.ibrestplus import api
from pyinfraboxutils.token import encode_global_token

ns = api.namespace('UserGlobalTokens',
                   path='/api/v1/user/global-tokens',
                   description='Personal viewer token management')

global_token_model = api.model('UserGlobalToken', {
    'id': fields.String,
    'description': fields.String,
    'scope_pull': fields.Boolean,
    'scope_push': fields.Boolean,
    'created_at': fields.String,
})

global_token_create_model = api.model('UserGlobalTokenCreate', {
    'description': fields.String(required=True),
    'scope_push': fields.Boolean(required=False, default=False),
    'scope_pull': fields.Boolean(required=False, default=True),
})

access_log_model = api.model('GlobalTokenAccessLog', {
    'accessed_at': fields.String,
    'path': fields.String,
    'method': fields.String,
    'status_code': fields.Integer,
})


def _serialize_row(row):
    result = {}
    for k, v in row.items():
        result[k] = v.isoformat() if isinstance(v, datetime) else v
    return result


@api.route('/api/v1/user/global-tokens', doc=False)
class UserGlobalTokens(Resource):

    def get(self):
        user_id = g.token['user']['id']
        tokens = g.db.execute_many_dict('''
            SELECT id, description, scope_push, scope_pull, created_at
            FROM global_token
            WHERE user_id = %s
            ORDER BY created_at DESC
        ''', [user_id])
        return [_serialize_row(t) for t in tokens]

    @api.expect(global_token_create_model, validate=True)
    def post(self):
        user_id = g.token['user']['id']
        body = request.get_json()
        token_id = str(uuid.uuid4())
        description = body['description']
        scope_push = body.get('scope_push', False)
        scope_pull = body.get('scope_pull', True)

        g.db.execute('''
            INSERT INTO global_token (id, description, scope_push, scope_pull, user_id)
            VALUES (%s, %s, %s, %s, %s)
        ''', [token_id, description, scope_push, scope_pull, user_id])
        g.db.commit()

        token = encode_global_token(token_id)

        return {
            'id': token_id,
            'token': token,
            'description': description,
            'scope_push': scope_push,
            'scope_pull': scope_pull,
        }


@api.route('/api/v1/user/global-tokens/<token_id>', doc=False)
class UserGlobalToken(Resource):

    def delete(self, token_id):
        user_id = g.token['user']['id']

        existing = g.db.execute_one('''
            SELECT id FROM global_token WHERE id = %s AND user_id = %s
        ''', [token_id, user_id])

        if not existing:
            return {'status': 404, 'message': 'Token not found'}, 404

        g.db.execute('''
            DELETE FROM global_token WHERE id = %s AND user_id = %s
        ''', [token_id, user_id])
        g.db.commit()

        return OK("OK")


@api.route('/api/v1/user/global-tokens/<token_id>/access-log', doc=False)
class UserGlobalTokenAccessLog(Resource):

    def get(self, token_id):
        user_id = g.token['user']['id']

        token = g.db.execute_one('''
            SELECT id FROM global_token WHERE id = %s AND user_id = %s
        ''', [token_id, user_id])

        if not token:
            return {'status': 404, 'message': 'Token not found'}, 404

        logs = g.db.execute_many_dict('''
            SELECT accessed_at, path, method, status_code
            FROM global_token_access_log
            WHERE token_id = %s
            ORDER BY accessed_at DESC
            LIMIT 200
        ''', [token_id])

        return [_serialize_row(log) for log in logs]
