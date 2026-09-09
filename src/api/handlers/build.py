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
    def get(self, project_id):
        '''
        Returns build summaries with aggregated state, dates, commit and PR info.
        Accepts: from, to, sha, branch, cronjob, state, size/build_limit
        '''

        build_from = request.args.get('from', None)
        build_to = request.args.get('to', None)
        sha = request.args.get('sha', None)
        branch = request.args.get('branch', None)
        cronjob = request.args.get('cronjob', None)
        state = request.args.get('state', None)
        size = request.args.get('build_limit', request.args.get('size', 10))

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

        rows = g.db.execute_many_dict('''
            SELECT
                b.id,
                b.build_number,
                b.restart_counter,
                b.is_cronjob,
                CASE
                    WHEN bool_or(j.state IN ('queued', 'scheduled', 'running')
                                 AND NOT j.restarted) THEN 'running'
                    WHEN bool_or(j.state = 'killed'   AND NOT j.restarted) THEN 'killed'
                    WHEN bool_or(j.state = 'error'    AND NOT j.restarted) THEN 'error'
                    WHEN bool_or(j.state = 'failure'  AND NOT j.restarted) THEN 'failure'
                    WHEN bool_or(j.state = 'unstable' AND NOT j.restarted) THEN 'unstable'
                    ELSE 'finished'
                END AS state,
                to_char(min(j.start_date), 'YYYY-MM-DD HH24:MI:SS') AS start_date,
                to_char(max(j.end_date),   'YYYY-MM-DD HH24:MI:SS') AS end_date,
                c.id          AS commit_id,
                c.branch      AS commit_branch,
                c.author_name AS commit_author_name,
                c.tag         AS commit_tag,
                c.url         AS commit_url,
                su.filename   AS source_upload_filename,
                pr.title      AS pull_request_title,
                pr.url        AS pull_request_url
            FROM build b
            LEFT JOIN job j            ON j.build_id        = b.id
            LEFT JOIN commit c         ON b.commit_id       = c.id
            LEFT JOIN source_upload su ON b.source_upload_id = su.id
            LEFT JOIN pull_request pr  ON c.pull_request_id  = pr.id
            WHERE b.project_id = %(pid)s
            AND b.build_number < %(to)s
            AND b.build_number >= %(from)s
            AND (%(sha)s     IS NULL OR c.id         = %(sha)s)
            AND (%(branch)s  IS NULL OR c.branch     = %(branch)s)
            AND (%(cronjob)s IS NULL OR b.is_cronjob = %(cronjob)s)
            AND (%(state)s   IS NULL OR EXISTS (
                SELECT 1 FROM job jf WHERE jf.build_id = b.id AND jf.state = %(state)s
            ))
            GROUP BY b.id, b.build_number, b.restart_counter, b.is_cronjob,
                     c.id, c.branch, c.author_name, c.tag, c.url,
                     su.filename, pr.title, pr.url
            ORDER BY b.build_number DESC, b.restart_counter DESC
            LIMIT %(size)s
        ''', {
            'pid': project_id,
            'from': build_from,
            'to': build_to,
            'sha': sha,
            'branch': branch,
            'cronjob': cronjob,
            'state': state,
            'size': size,
        })

        result = []
        for b in rows:
            o = {
                'id': b['id'],
                'build_number': b['build_number'],
                'restart_counter': b['restart_counter'],
                'is_cronjob': b['is_cronjob'],
                'state': b['state'],
                'start_date': b['start_date'],
                'end_date': b['end_date'],
                'commit': None,
                'source_upload': None,
                'pull_request': None,
            }
            if b['commit_id']:
                o['commit'] = {
                    'id': b['commit_id'],
                    'branch': b['commit_branch'],
                    'author_name': b['commit_author_name'],
                    'tag': b['commit_tag'],
                    'url': b['commit_url'],
                }
            if b['source_upload_filename']:
                o['source_upload'] = {'filename': b['source_upload_filename']}
            if b['pull_request_title']:
                o['pull_request'] = {
                    'title': b['pull_request_title'],
                    'url': b['pull_request_url'],
                }
            result.append(o)
        return result

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
