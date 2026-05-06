import uuid

from flask import g, abort, request
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


@api.route('/api/v1/user/global-tokens', doc=False)
class UserGlobalTokens(Resource):

    def get(self):
        """List the current user's global viewer tokens"""
        user_id = g.token['user']['id']
        tokens = g.db.execute_many_dict('''
            SELECT id, description, scope_push, scope_pull, created_at
            FROM global_token
            WHERE user_id = %s
            ORDER BY created_at DESC
        ''', [user_id])
        return tokens

    @api.expect(global_token_create_model, validate=True)
    def post(self):
        """Create a new global viewer token for the current user"""
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
        """Revoke one of the current user's global tokens"""
        user_id = g.token['user']['id']

        num = g.db.execute('''
            DELETE FROM global_token
            WHERE id = %s AND user_id = %s
        ''', [token_id, user_id])
        g.db.commit()

        if num == 0:
            abort(404, "Token not found")

        return OK("OK")


@api.route('/api/v1/user/global-tokens/<token_id>/access-log', doc=False)
class UserGlobalTokenAccessLog(Resource):

    def get(self, token_id):
        """Return the last 200 access log entries for one of the user's tokens"""
        user_id = g.token['user']['id']

        # Verify ownership before exposing access log
        token = g.db.execute_one('''
            SELECT id FROM global_token
            WHERE id = %s AND user_id = %s
        ''', [token_id, user_id])

        if not token:
            abort(404, "Token not found")

        logs = g.db.execute_many_dict('''
            SELECT accessed_at, path, method, status_code
            FROM global_token_access_log
            WHERE token_id = %s
            ORDER BY accessed_at DESC
            LIMIT 200
        ''', [token_id])

        return logs
