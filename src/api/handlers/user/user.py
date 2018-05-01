from flask import g, abort
from flask_restplus import Resource

from pyinfraboxutils.ibflask import auth_required, OK
from pyinfraboxutils.ibrestplus import api

ns = api.namespace('api/v1/user',
                   description="Users related operations")

@ns.route('/')
class User(Resource):

    @auth_required(['user'], check_project_access=False)
    def get(self):
        user = g.db.execute_one_dict('''
            SELECT github_id, username, avatar_url, name, email, id
            FROM "user"
            WHERE id = %s
        ''', [g.token['user']['id']])

        if not user:
            abort(404)

        return user
