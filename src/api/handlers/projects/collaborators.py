from flask import request, g, abort
from flask_restplus import Resource, fields

from pyinfraboxutils.ibflask import auth_required, OK
from pyinfraboxutils.ibrestplus import api

from api.namespaces import project as ns

collaborator_model = api.model('Collaborator', {
    'name': fields.String(required=True),
    'id': fields.String(required=False),
    'email': fields.String(required=False),
    'avatar_url': fields.String(required=False),
    'username': fields.String(required=False)
})

add_collaborator_model = api.model('AddCollaborator', {
    'username': fields.String(required=True)
})


@ns.route('/<project_id>/collaborators/')
class Collaborators(Resource):

    @auth_required(['user'])
    @api.marshal_list_with(collaborator_model)
    def get(self, project_id):
        p = g.db.execute_many_dict(
            """
            SELECT u.name, u.id, u.email, u.avatar_url, u.username FROM "user" u
            INNER JOIN collaborator co
                ON co.user_id = u.id
                AND co.project_id = %s
        """, [project_id])

        return p

    @auth_required(['user'], check_project_owner=True)
    @api.expect(add_collaborator_model)
    def post(self, project_id):
        b = request.get_json()
        username = b['username']

        user = g.db.execute_one_dict(
            """
            SELECT * FROM "user"
            WHERE username = %s
        """, [username])

        if not user:
            abort(400, "User not found.")

        num_collaborators = g.db.execute_one(
            """
            SELECT COUNT(*) FROM collaborator
            WHERE user_id = %s
            AND project_id = %s
        """, [user['id'], project_id])[0]

        if num_collaborators != 0:
            return OK('Specified user is already a collaborator.')

        g.db.execute(
            """
            INSERT INTO collaborator (project_id, user_id)
            VALUES(%s, %s) ON CONFLICT DO NOTHING
        """, [project_id, user['id']])

        g.db.commit()

        return OK('Successfully added user')


@ns.route('/<project_id>/collaborators/<user_id>')
class Collaborator(Resource):

    @auth_required(['user'], check_project_owner=True)
    def delete(self, project_id, user_id):
        owner_id = g.token['user']['id']

        if user_id == owner_id:
            abort(400, "It's not allowed to delete the owner of the project from collaborators.")

        num_collaborators = g.db.execute_one(
            """
            SELECT COUNT(*) FROM collaborator
            WHERE user_id = %s
            AND project_id = %s
        """, [user_id, project_id])[0]

        # Give some warning if the specified user has been already removed
        # from the collaborators or has been never added there before
        if num_collaborators == 0:
            return OK('Specified user is not in collaborators list.')

        g.db.execute(
            """
            DELETE FROM collaborator
            WHERE user_id = %s
            AND project_id = %s
        """, [user_id, project_id])

        g.db.commit()

        return OK('Successfully removed user')
