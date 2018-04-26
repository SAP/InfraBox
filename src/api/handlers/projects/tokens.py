from flask import request, g, abort
from flask_restplus import Resource, fields

from pyinfrabox.utils import validate_uuid4
from pyinfraboxutils.ibflask import auth_required, OK
from pyinfraboxutils.ibrestplus import api
from pyinfraboxutils.token import encode_project_token
from api.namespaces import project as ns

project_token_model = api.model('ProjectToken', {
    'description': fields.String(required=True),
    'scope_push': fields.Boolean(required=True),
    'scope_pull': fields.Boolean(required=True),
    'id': fields.String(required=False)
})

@ns.route('/<project_id>/tokens')
class Tokens(Resource):

    @auth_required(['user'])
    @api.marshal_list_with(project_token_model)
    def get(self, project_id):
        p = g.db.execute_many_dict('''
            SELECT description, scope_push, scope_pull, id
            FROM auth_token
            WHERE project_id = %s
        ''', [project_id])
        return p


    @auth_required(['user'])
    @api.expect(project_token_model)
    def post(self, project_id):
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
        token = encode_project_token(token_id, project_id)

        g.db.commit()

        return OK('Successfully added token.', {'token': token})

@ns.route('/<project_id>/tokens/<token_id>')
class Token(Resource):

    @auth_required(['user'])
    def delete(self, project_id, token_id):
        if not validate_uuid4(token_id):
            abort(400, "Invalid project-token uuid.")

        num_tokens = g.db.execute_one("""
            SELECT COUNT(*) FROM auth_token
            WHERE project_id = %s and id = %s
        """, [project_id, token_id])[0]

        if num_tokens == 0:
            return abort(400, 'Such token does not exist.')

        g.db.execute("""
                     DELETE FROM auth_token
                     WHERE project_id = %s and id = %s
        """, [project_id, token_id])
        g.db.commit()

        return OK('Successfully deleted token.')
