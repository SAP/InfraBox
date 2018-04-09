from flask import g, abort, request
from flask_restplus import Resource, fields

from pyinfraboxutils.ibflask import auth_required

from api.namespaces import admin as ns

@ns.route('/users/')
class Users(Resource):

    @auth_required(['user'], check_admin=True)
    def get(self):
        users = g.db.execute_many_dict('''
            SELECT name, username, email, avatar_url
            FROM "user"
            ORDER BY name
        ''')

        return users
