import uuid

from flask import g, abort, request
from flask_restx import Resource, fields
from pyinfraboxutils.ibflask import OK
from pyinfraboxutils.ibrestplus import api
from pyinfraboxutils.token import encode_global_token

global_token_create_model = api.model('GlobalTokenCreate', {
    'description': fields.String(required=True),
    'scope_push': fields.Boolean(required=False, default=False),
    'scope_pull': fields.Boolean(required=False, default=True),
})

@api.route('/api/v1/admin/global-tokens', doc=False)
class GlobalTokens(Resource):

    def get(self):
        """List all global tokens (admin only)"""
        tokens = g.db.execute_many_dict('''
            SELECT id, description, scope_push, scope_pull
            FROM global_token
            ORDER BY description
        ''')
        return tokens

    @api.expect(global_token_create_model, validate=True)
    def post(self):
        """Create a new global token (admin only)"""
        if g.token['user']['role'] != 'admin':
            abort(403, "creating global tokens is only allowed for admin users")

        body = request.get_json()
        token_id = str(uuid.uuid4())
        description = body['description']
        scope_push = body.get('scope_push', False)
        scope_pull = body.get('scope_pull', True)

        g.db.execute('''
            INSERT INTO global_token (id, description, scope_push, scope_pull)
            VALUES (%s, %s, %s, %s)
        ''', [token_id, description, scope_push, scope_pull])
        g.db.commit()

        token = encode_global_token(token_id)

        return {
            'id': token_id,
            'token': token,
            'description': description,
            'scope_push': scope_push,
            'scope_pull': scope_pull,
        }


@api.route('/api/v1/admin/global-tokens/<token_id>', doc=False)
class GlobalToken(Resource):

    def get(self, token_id):
        """Get a specific global token (admin only)"""
        token = g.db.execute_one_dict('''
            SELECT id, description, scope_push, scope_pull
            FROM global_token
            WHERE id = %s
        ''', [token_id])

        if not token:
            abort(404, "Global token not found")

        return token

    def delete(self, token_id):
        """Delete a global token (admin only)"""
        if g.token['user']['role'] != 'admin':
            abort(403, "deleting global tokens is only allowed for admin users")

        num = g.db.execute('''
            DELETE FROM global_token WHERE id = %s
        ''', [token_id])
        g.db.commit()

        if num == 0:
            abort(404, "Global token not found")

        return OK("OK")