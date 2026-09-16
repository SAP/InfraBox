from flask import g, request
from flask_restx import Resource, fields

from pyinfraboxutils.ibrestplus import api

from api.handlers.job import job_model

ns = api.namespace('Builds',
                   path='/api/v1/projects/<project_id>/builds/',
                   description='Build related operations',
                   params={'project_id': 'The project ID', 'build_id': 'The build ID'})

build_model = api.model('BuildModel', {
    'id': fields.String,
    'build_number': fields.Integer,
    'restart_counter': fields.Integer
})

@ns.route('/')
@api.doc(responses={403: 'Not Authorized'})
class Builds(Resource):
    @api.marshal_list_with(build_model)
    def get(self, project_id):
        '''
        Returns builds
        '''

        build_from = request.args.get('from', None)
        build_to = request.args.get('to', None)
        sha = request.args.get('sha', None)
        branch = request.args.get('branch', None)
        cronjob = request.args.get('cronjob', None)
        size = request.args.get('size', 10)

        if cronjob == "true":
            cronjob = True
        elif cronjob == "false":
            cronjob = False
        else:
            cronjob = None

        if build_from:
            build_from = int(build_from)

        if build_to:
            build_to = int(build_to)

        size = min(50, max(int(size), 0))

        if not build_to:
            r = g.db.execute_one_dict('''
                SELECT max(build_number) as max
                FROM build
                WHERE project_id = %s
            ''', [project_id])

            if not r or not r['max']:
                build_to = 1
            else:
                build_to = r['max'] + 1

        if not build_from:
            build_from = 0

        #if build_to - build_from > 500:
        #    build_from = max(build_to - 500, 0)

        p = g.db.execute_many_dict('''
            SELECT b.id, b.build_number, b.restart_counter, b.is_cronjob
            FROM build b
            LEFT OUTER JOIN commit c
            ON b.commit_id = c.id
            WHERE b.project_id = %(pid)s
            AND b.build_number < %(to)s
            AND b.build_number >= %(from)s
            AND (%(sha)s IS NULL OR c.id = %(sha)s)
            AND (%(branch)s IS NULL OR c.branch = %(branch)s)
            AND (%(cronjob)s IS NULL OR b.is_cronjob = %(cronjob)s)
            ORDER BY build_number DESC, restart_counter DESC
            LIMIT %(size)s
        ''', {
            'pid': project_id,
            'from': build_from,
            'to': build_to,
            'sha': sha,
            'branch': branch,
            'cronjob': cronjob,
            'size': size,
        })

        return p

@ns.route('/<build_id>')
@api.doc(responses={403: 'Not Authorized'})
class Build(Resource):
    @api.marshal_with(build_model)
    def get(self, project_id, build_id):
        '''
        Returns a single build
        '''
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
@api.doc(responses={403: 'Not Authorized'})
class Jobs(Resource):

    @api.marshal_list_with(job_model)
    def get(self, project_id, build_id):
        '''
        Returns alls jobs of a build
        '''
        jobs = g.db.execute_many_dict('''
            SELECT id, state, start_date, build_id, end_date, name, type,
                definition#>'{resources,limits,cpu}' as cpu,
                definition#>'{resources,limits,memory}' as memory,
                build_arg, env_var, message, dockerfile as docker_file,
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
