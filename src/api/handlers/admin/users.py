from flask import g, abort, request
from flask_restplus import Resource, fields


from api.namespaces import admin as ns

@ns.route('/users/')
class Users(Resource):

    def get(self):
        users = g.db.execute_many_dict('''
            SELECT name, username, email, avatar_url
            FROM "user"
            ORDER BY name
        ''')

        return users
