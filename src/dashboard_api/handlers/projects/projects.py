from flask import g, abort
from flask_restplus import Resource

from pyinfraboxutils.ibflask import auth_token_required, OK

from dashboard_api import project_ns as ns

@ns.route('/<project_id>/')
class Project(Resource):

    @auth_token_required(['user'], check_project_owner=True)
    def delete(self, project_id):

        project = g.db.execute_one_dict('''
            DELETE FROM project WHERE id = %s RETURNING type
        ''', [project_id])

        if not project:
            abort(404)


        if project['type'] == 'github':
            repo = g.db.execute_one_dict('''
                SELECT name, github_owner, github_hook_id
                FROM repository
                WHERE project_id = %s
            ''', [project_id])

            user = g.db.execute_one_dict('''
                SELECT github_api_token
                FROM "user"
                WHERE id = %s
            ''', [g.token['user']['id']])


            # TODO: Delete hook
            assert False

        # TODO: delete all tables
        g.db.execute('''
            DELETE FROM repository
            WHERE project_id = %s
        ''', [project_id])

        g.db.execute('''
            DELETE FROM collaborator
            WHERE project_id = %s
        ''', [project_id])


        g.db.commit()

        return OK('deleted project')
