from flask import g
from flask_restplus import Resource

from pyinfraboxutils.ibflask import auth_required
from pyinfraboxutils.ibrestplus import api

ns = api.namespace('Commits',
                   path='/api/v1/projects/<project_id>/commits',
                   description='Commit related operations',
                   doc=False)

@ns.route('/<commit_id>', doc=False)
@api.response(403, 'Not Authorized')
class Commit(Resource):

    @auth_required(['user'], allow_if_public=True)
    def get(self, project_id, commit_id):
        p = g.db.execute_many_dict('''
            SELECT c.* FROM commit c
            WHERE c.id = %s
            AND c.project_id = %s
        ''', [commit_id, project_id])
        return p
