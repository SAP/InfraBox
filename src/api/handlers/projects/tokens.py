from flask import request, g, abort
from flask_restx import Resource, fields

from pyinfrabox.utils import validate_uuid
from pyinfraboxutils.ibflask import OK
from pyinfraboxutils.ibrestplus import api, response_model
from pyinfraboxutils.token import encode_project_token

ns = api.namespace('Tokens',
                   path='/api/v1/projects/<project_id>/tokens',
                   description='Token related operations')

project_token_model = api.model('ProjectToken', {
    'description': fields.String(required=True),
    'scope_push': fields.Boolean(required=True),
    'scope_pull': fields.Boolean(required=True),
    'id': fields.String(required=False)
})

@ns.route('/')
@api.doc(responses={403: 'Not Authorized'})
class Tokens(Resource):

    @api.marshal_list_with(project_token_model)
    def get(self, project_id):
        '''
        Returns project's tokens
        '''
        p = g.db.execute_many_dict('''
            SELECT description, scope_push, scope_pull, id
            FROM auth_token
            WHERE project_id = %s
        ''', [project_id])
        return p

    @api.expect(project_token_model)
    @api.response(200, 'Success', response_model)
    def post(self, project_id):
        '''
        Create new token
        '''
        project_name = g.db.execute_one("""
            SELECT name FROM project
            WHERE id = %s
        """, [project_id])
        if not project_name:
            return abort(400, 'Invalid project id.')

        b = request.get_json()

        result = g.db.execute_one("""
            SELECT COUNT(*) FROM auth_token
            WHERE project_id = %s AND description = %s
        """, [project_id, b['description']])[0]

        if result != 0:
            return abort(400, 'Token with such a description already exists.')

        result = g.db.execute_one_dict("""
            INSERT INTO auth_token (description, scope_push, scope_pull, project_id)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, [b['description'], b['scope_push'], b['scope_pull'], project_id])

        token_id = result['id']
        token = encode_project_token(token_id, project_id, project_name)

        g.db.commit()

        return OK('Successfully added token.', {'token': token})

@ns.route('/<token_id>')
@api.doc(responses={403: 'Not Authorized'})
@api.doc(responses={404: 'Token not found'})
class Token(Resource):

    @api.response(200, 'Success', response_model)
    def delete(self, project_id, token_id):
        '''
        Delete a token
        '''
        if not validate_uuid(token_id):
            abort(400, "Invalid project-token uuid.")

        num_tokens = g.db.execute_one("""
            SELECT COUNT(*) FROM auth_token
            WHERE project_id = %s and id = %s
        """, [project_id, token_id])[0]

        if num_tokens == 0:
            return abort(404, 'Such token does not exist.')

        g.db.execute("""
                     DELETE FROM auth_token
                     WHERE project_id = %s and id = %s
        """, [project_id, token_id])
        g.db.commit()

        return OK('Successfully deleted token.')
