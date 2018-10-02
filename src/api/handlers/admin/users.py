from flask import g
from flask_restplus import Resource

from pyinfraboxutils.ibrestplus import api
from pyinfraboxutils.ibflask import auth_required

@api.route('/api/v1/admin/users', doc=False)
class Users(Resource):

    @auth_required(['user'], check_admin=True)
    def get(self):
        users = g.db.execute_many_dict('''
            SELECT name, username, email, avatar_url
            FROM "user"
            ORDER BY name
        ''')

        return users
