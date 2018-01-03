from flask import g
from flask_restplus import Resource, fields

from pyinfraboxutils.ibflask import auth_token_required
from pyinfraboxutils.ibrestplus import api

ns = api.namespace('api/v1/projects/<project_id>/builds', description='Build related operations')

build_model = api.model('BuildModel', {
    'id': fields.String,
    'build_number': fields.Integer,
    'restart_counter': fields.Integer
})

@ns.route('/')
class Builds(Resource):
    @auth_token_required(['user', 'project'])
    @api.marshal_list_with(build_model)
    def get(self, project_id):
        p = g.db.execute_many_dict('''
            SELECT id, build_number, restart_counter
            FROM build
            WHERE project_id = %s
            ORDER BY build_number DESC, restart_counter DESC
            LIMIT 100
        ''', [project_id])
        return p

@ns.route('/<build_id>')
class Build(Resource):
    @auth_token_required(['user', 'project'])
    @api.marshal_with(build_model)
    def get(self, project_id, build_id):
        p = g.db.execute_many_dict('''
            SELECT id, build_number, restart_counter
            FROM build
            WHERE project_id = %s
            AND id = %s
            ORDER BY build_number DESC, restart_counter DESC
            LIMIT 100
        ''', [project_id, build_id])
        return p
