from flask import g, abort
from flask_restplus import Resource, fields

from pyinfraboxutils.ibrestplus import api
from pyinfraboxutils.ibflask import auth_required, OK

from dashboard_api.namespaces import project as ns

project_model = api.model('Project', {
    'id': fields.String(required=True),
    'name': fields.String(required=True),
    'type': fields.String(required=True)
})

@ns.route('/')
class Projects(Resource):

    @auth_required(['user'], check_project_access=False)
    @api.marshal_list_with(project_model)
    def get(self):
        projects = g.db.execute_many_dict('''
            SELECT p.id, p.name, p.type FROM project p
            INNER JOIN collaborator co
            ON co.project_id = p.id
            AND %s = co.user_id
            ORDER BY p.name
        ''', [g.token['user']['id']])

        return projects

@ns.route('/name/<project_name>')
class ProjectName(Resource):

    @auth_required(['user'], check_project_access=False, allow_if_public=True)
    @api.marshal_list_with(project_model)
    def get(self, project_name):
        project = g.db.execute_one_dict('''
            SELECT id, name, type
            FROM project
            WHERE name = %s
        ''', [project_name])

        if not project:
            abort(404)

        return project


@ns.route('/<project_id>/')
class Project(Resource):

    @auth_required(['user'], allow_if_public=True)
    @api.marshal_list_with(project_model)
    def get(self, project_id):
        projects = g.db.execute_many_dict('''
            SELECT p.id, p.name, p.type
            FROM project p
            WHERE id = %s
        ''', [project_id])

        return projects

    @auth_required(['user'], check_project_owner=True)
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
