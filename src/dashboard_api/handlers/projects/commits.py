from flask import g
from flask_restplus import Resource

from pyinfraboxutils.ibflask import auth_required

from dashboard_api.namespaces import project as ns

@ns.route('/<project_id>/commits/<commit_id>')
class Copmmit(Resource):

    @auth_required(['user'], allow_if_public=True)
    def get(self, project_id, commit_id):
        p = g.db.execute_many_dict('''
            SELECT c.* FROM commit c
            WHERE c.id = %s
            AND c.project_id = %s
        ''', [commit_id, project_id])
        return p
