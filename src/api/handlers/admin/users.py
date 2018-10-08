from flask import g
from flask_restplus import Resource

from pyinfraboxutils.ibrestplus import api

@api.route('/api/v1/admin/users', doc=False)
class Users(Resource):

    def get(self):
        users = g.db.execute_many_dict('''
            SELECT name, username, email, avatar_url
            FROM "user"
            ORDER BY name
        ''')

        return users
