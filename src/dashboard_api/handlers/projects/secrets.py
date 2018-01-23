from flask import request, g, abort
from flask_restplus import Resource, fields

from pyinfraboxutils.ibflask import auth_token_required, OK
from pyinfraboxutils.ibrestplus import api

from dashboard_api import project_ns as ns

secret_model = api.model('Secret', {
    'name': fields.String(required=True),
    'id': fields.String(required=True),
})

add_secret_model = api.model('AddSecret', {
    'name': fields.String(required=True),
    'value': fields.String(required=True),
})

@ns.route('/<project_id>/secrets')
class Secrets(Resource):

    @auth_token_required(['user'])
    @api.marshal_list_with(secret_model)
    def get(self, project_id):
        p = g.db.execute_many_dict('''
            SELECT name, id FROM secret
            WHERE project_id = %s
        ''', [project_id])
        return p

    @auth_token_required(['user'])
    @api.expect(add_secret_model)
    def post(self, project_id):
        b = request.get_json()

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

@ns.route('/<project_id>/secrets/<secret_id>')
class Secret(Resource):

    @auth_token_required(['user'])
    def delete(self, project_id, secret_id):
        g.db.execute('''
            DELETE FROM secret WHERE project_id = %s and id = %s
        ''', [project_id, secret_id])
        g.db.commit()

        return OK('Successfully deleted secret')
