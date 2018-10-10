from uuid import UUID

from flask import request, g, abort
from flask_restplus import Resource, fields

from pyinfraboxutils.ibflask import OK
from pyinfraboxutils.ibrestplus import api, response_model

ns = api.namespace('Collaborators',
                   path='/api/v1/projects/<project_id>/collaborators',
                   description='Collaborator related operations')

collaborator_model = api.model('Collaborator', {
    'name': fields.String(required=True),
    'id': fields.String(required=False),
    'email': fields.String(required=False),
    'avatar_url': fields.String(required=False),
    'username': fields.String(required=False),
    'role': fields.String(required=False)
})

add_collaborator_model = api.model('AddCollaborator', {
    'username': fields.String(required=True),
    'role': fields.String(required=False)
})

change_collaborator_model = api.model('AddCollaborator', {
    'role': fields.String(required=True)
})

@ns.route('/')
@api.response(403, 'Not Authorized')
class Collaborators(Resource):

    @api.marshal_list_with(collaborator_model)
    def get(self, project_id):
        '''
        Returns all collaborators
        '''
        p = g.db.execute_many_dict(
            """
            SELECT u.name, u.id, u.email, u.avatar_url, u.username, co.role FROM "user" u
            INNER JOIN collaborator co
                ON co.user_id = u.id
                AND co.project_id = %s
        """, [project_id])

        return p

    @api.expect(add_collaborator_model)
    @api.response(200, 'Success', response_model)
    def post(self, project_id):
        '''
        Add a collaborator
        '''
        b = request.get_json()
        username = b['username']
        userrole = b['role'] if 'role' in b else 'Developer'

        # Prevent for now a project owner change
        # (Because with GitHub Integration the project owner's GitHub Token will be used)
        if userrole == 'Owner':
            abort(403, "A project is limited to one owner.")

        user = g.db.execute_one_dict(
            """
            SELECT * FROM "user"
            WHERE username = %s
        """, [username])

        if not user:
            abort(400, "User not found.")

        roles = g.db.execute_many(
            """
            SELECT unnest(enum_range(NULL::user_role))
        """)

        if [userrole] not in roles:
            abort(400, "Role unknown.")

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
            INSERT INTO collaborator (project_id, user_id, role)
            VALUES(%s, %s, %s) ON CONFLICT DO NOTHING
        """, [project_id, user['id'], userrole])
        g.db.commit()

        # Updated collaborator data will be pushed with next push cycle to OPA

        return OK('Successfully added user.')

@ns.route('/roles')
class CollaboratorRoles(Resource):
    def get(self, project_id):
        roles = g.db.execute_many("""
            SELECT unnest(enum_range(NULL::user_role))
        """)

        return [role[0] for role in roles]

@ns.route('/<uuid:user_id>')
class Collaborator(Resource):

    @api.expect(change_collaborator_model)
    @api.response(200, 'Success', response_model)
    def put(self, project_id, user_id):

        # Prevent for now a project owner change
        # (Because with GitHub Integration the project owner's GitHub Token will be used)
        if user_id.hex == UUID(g.token['user']['id']).hex:
            abort(403, "A project must have an owner.")

        # Ensure that user is already a collaborator
        num_collaborators = g.db.execute_one(
            """
            SELECT COUNT(*) FROM collaborator
            WHERE user_id = %s
            AND project_id = %s
        """, [str(user_id), project_id])[0]
        if num_collaborators == 0:
            abort(400, 'Specified user is not in collaborators list.')

        b = request.get_json()
        userrole = b['role']

        if userrole == "Owner":
            abort(403, "A project is limited to one owner.")

        # Ensure that role is valid
        roles = g.db.execute_many(
            """
            SELECT unnest(enum_range(NULL::user_role))
        """)
        if [userrole] not in roles:
            abort(400, "Role unknown.")

        # Do update
        g.db.execute(
            """
            UPDATE collaborator
            SET role = %s
            WHERE user_id = %s
            AND project_id = %s
        """, [userrole, str(user_id), project_id])

        g.db.commit()

        # Updated collaborator data will be pushed with next push cycle to OPA

        return OK('Successfully changed user role.')

    @api.response(200, 'Success', response_model)
    def delete(self, project_id, user_id):
        '''
        Remove collaborator from project
        '''
        owner_id = g.token['user']['id']

        if user_id.hex == UUID(owner_id).hex:
            abort(400, "It's not allowed to delete the owner of the project from collaborators.")

        num_collaborators = g.db.execute_one(
            """
            SELECT COUNT(*) FROM collaborator
            WHERE user_id = %s
            AND project_id = %s
        """, [str(user_id), project_id])[0]

        # Give some warning if the specified user has been already removed
        # from the collaborators or has been never added there before
        if num_collaborators == 0:
            return OK('Specified user is not in collaborators list.')

        g.db.execute(
            """
            DELETE FROM collaborator
            WHERE user_id = %s
            AND project_id = %s
        """, [str(user_id), project_id])

        g.db.commit()

        # Updated collaborator data will be pushed with next push cycle to OPA

        return OK('Successfully removed user.')
