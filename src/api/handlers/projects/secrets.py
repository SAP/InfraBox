from flask import request, g, abort
from flask_restplus import Resource, fields
import re

from pyinfraboxutils.ibflask import auth_required, OK
from pyinfraboxutils.ibrestplus import api

secret_model = api.model('Secret', {
    'name': fields.String(required=True),# pattern='^[a-zA-Z0-9_]*$'),
    'id': fields.String(required=True),
})

add_secret_model = api.model('AddSecret', {
    'name': fields.String(required=True),# pattern='^[a-zA-Z0-9_]*$'),
    'value': fields.String(required=True),
})

ns = api.namespace('api/v1/projects/<project_id>/secrets',
                   description="Project's secrets managing")

@ns.route('/')
class Secrets(Resource):

    name_pattern = re.compile('^[a-zA-Z0-9_]+$')

    @auth_required(['user'])
    @api.marshal_list_with(secret_model)
    def get(self, project_id):
        p = g.db.execute_many_dict('''
            SELECT name, id FROM secret
            WHERE project_id = %s
        ''', [project_id])
        return p

    @auth_required(['user'])
    @api.expect(add_secret_model)
    def post(self, project_id):
        b = request.get_json()

        if not Secrets.name_pattern.match(b['name']):
            abort(400, 'Secret name must be not empty alphanumeric string')

        result = g.db.execute_one_dict('''
            SELECT COUNT(*) as cnt FROM secret WHERE project_id = %s
        ''', [project_id])

        if result['cnt'] > 50:
            abort(400, 'too many secrets')

        g.db.execute('''
            INSERT INTO secret (project_id, name, value) VALUES(%s, %s, %s)
        ''', [project_id, b['name'], b['value']])

        g.db.commit()

        return OK('Successfully added secret')

@ns.route('/<secret_id>')
class Secret(Resource):

    @auth_required(['user'])
    def delete(self, project_id, secret_id):
        g.db.execute('''
            DELETE FROM secret WHERE project_id = %s and id = %s
        ''', [project_id, secret_id])
        g.db.commit()

        return OK('Successfully deleted secret')
