from flask import g, abort, request
from flask_restx import Resource, fields
from pyinfraboxutils.ibflask import OK

from pyinfraboxutils.ibrestplus import api

user_role_setting_model = api.model('UserRoleUpdate', {
    'id': fields.String(required=True),
    'role': fields.String(required=True, enum=['user', 'devops', 'admin']),
})

@api.route('/api/v1/admin/users', doc=False)
class Users(Resource):

    def get(self):
        users = g.db.execute_many_dict('''
            SELECT id, name, username, email, avatar_url, role
            FROM "user"
            ORDER BY name
        ''')

        return users

    @api.expect(user_role_setting_model, validate=True)
    def post(self):
        if g.token['user']['role'] != 'admin':
            abort(403, "updating user role is only allowed for admin user")
        body = request.get_json()
        if body['id'] == '00000000-0000-0000-0000-000000000000':
            abort(403, "can't change role for Admin")
        g.db.execute('''
                   UPDATE "user"
                   SET role=%s
                   WHERE id=%s
               ''', [body['role'], body['id']])
        g.db.commit()
        return OK("OK")
