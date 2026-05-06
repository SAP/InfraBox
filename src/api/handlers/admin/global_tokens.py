from flask import g
from flask_restx import Resource

from pyinfraboxutils.ibrestplus import api


@api.route('/api/v1/admin/global-tokens', doc=False)
class AdminGlobalTokens(Resource):

    def get(self):
        """List all users' global tokens (admin audit view)"""
        tokens = g.db.execute_many_dict('''
            SELECT gt.id, gt.description, gt.scope_push, gt.scope_pull,
                   gt.created_at, u.username AS owner_username
            FROM global_token gt
            LEFT JOIN "user" u ON u.id = gt.user_id
            ORDER BY gt.created_at DESC
        ''')
        return tokens
