from flask import request, g
from flask_restplus import Resource, fields

from pyinfraboxutils.ibflask import auth_required, OK
from pyinfraboxutils.ibrestplus import api
from pyinfraboxutils.token import encode_project_token

project_token_model = api.model('ProjectToken', {
    'description': fields.String(required=True),
    'scope_push': fields.Boolean(required=True),
    'scope_pull': fields.Boolean(required=True),
    'id': fields.String(required=False)
})

ns = api.namespace('api/v1/projects/<project_id>/tokens',
                   description="Project's tokens managing")

@ns.route('/')
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

        result = g.db.execute_one_dict('''
            INSERT INTO auth_token (description, scope_push, scope_pull, project_id)
            VALUES (%s, %s, %s, %s) RETURNING id
        ''', [b['description'], b['scope_push'], b['scope_pull'], project_id])

        token_id = result['id']
        token = encode_project_token(token_id, project_id)

        g.db.commit()

        return OK('Successfully added token', {'token': token})

@ns.route('/<token_id>')
class Token(Resource):

    @auth_required(['user'])
    def delete(self, project_id, token_id):
        g.db.execute('''
            DELETE FROM auth_token
            WHERE project_id = %s and id = %s
        ''', [project_id, token_id])
        g.db.commit()

        return OK('Successfully deleted token')
