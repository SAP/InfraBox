from flask import g
from flask_restplus import Resource, fields

from pyinfraboxutils.ibflask import auth_required
from pyinfraboxutils.ibrestplus import api

from api.handlers.job import job_model

ns = api.namespace('api/v1/projects/<project_id>/builds', description='Build related operations')

build_model = api.model('BuildModel', {
    'id': fields.String,
    'build_number': fields.Integer,
    'restart_counter': fields.Integer
})

@ns.route('/')
class Builds(Resource):
    @auth_required(['user', 'project'])
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
    @auth_required(['user', 'project'])
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

@ns.route('/<build_id>/jobs')
class Jobs(Resource):

    @auth_required(['project'])
    @ns.marshal_list_with(job_model)
    def get(self, project_id, build_id):
        jobs = g.db.execute_many_dict('''
            SELECT id, state, start_date, build_id, end_date, name, type,
                cpu, memory, build_arg, env_var, message, dockerfile as docker_file,
                dependencies as depends_on
            FROM job
            WHERE project_id = %s
            AND build_id = %s
        ''', [project_id, build_id])

        for j in jobs:
            if j['type'] == 'run_docker_compose':
                j['type'] = 'docker_compose'
                j['docker_compose_file'] = j['docker_file']
                del j['docker_file']
            elif j['type'] == 'run_project_container':
                j['type'] = 'docker'
        return jobs
