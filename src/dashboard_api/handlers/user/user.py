from flask import g
from flask_restplus import Resource

from pyinfraboxutils.ibflask import auth_required

from dashboard_api.namespaces import user as ns

@ns.route('/')
class User(Resource):

    @auth_required(['user'], check_project_access=False)
    def get(self):
        jobs = g.db.execute_many_dict('''
            SELECT github_id, username, avatar_url, name, email
            FROM "user"
            WHERE id = %s
        ''', [g.token['user']['id']])

        return jobs
