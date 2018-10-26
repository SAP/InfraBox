import json
import os
import uuid
import re

from io import BytesIO

import requests

from flask import g, abort, Response, send_file, request
from flask_restplus import Resource, fields

from pyinfraboxutils import get_logger
from pyinfraboxutils.ibflask import OK
from pyinfraboxutils.ibrestplus import api, response_model
from pyinfraboxutils.storage import storage
from pyinfraboxutils.token import encode_user_token

logger = get_logger('api')

ns = api.namespace('Jobs',
                   path='/api/v1/projects/<project_id>/jobs/',
                   description='Commit related operations')


@ns.route('/', doc=False)
@api.response(403, 'Not Authorized')
class Jobs(Resource):

    def get(self, project_id):
        jobs = g.db.execute_many_dict('''
            WITH github_builds AS (
                --- get the last 10 builds for each branch
                SELECT builds.id, builds.project_id, builds.commit_id, null::uuid as source_upload_id, build_number, restart_counter FROM (
                    SELECT b.id, c.id as commit_id, p.id as project_id, ROW_NUMBER() OVER(PARTITION BY p.id ORDER BY build_number DESC, restart_counter DESC) AS r, build_number, restart_counter
                    FROM build b
                    INNER JOIN project p
                        ON b.project_id = %(pid)s
                        AND p.id = %(pid)s
                        AND p.type in ('github', 'gerrit')
                    LEFT OUTER JOIN commit c
                        ON b.commit_id = c.id
                        AND c.project_id = %(pid)s
                ) builds
                WHERE builds.r <= 10
            ), upload_builds AS (
                --- get the last 10 builds
                SELECT builds.id, builds.project_id, null::character varying as commit_id, builds.source_upload_id, build_number, restart_counter  FROM (
                    SELECT b.id, p.id as project_id, source_upload_id, ROW_NUMBER() OVER(PARTITION BY p.id ORDER BY build_number DESC, restart_counter DESC) AS r, build_number, restart_counter
                    FROM build b
                    INNER JOIN project p
                        ON p.id = %(pid)s
                        AND b.project_id = p.id
                        AND p.type = 'upload'
                ) builds
                WHERE builds.r <= 10
            ), builds AS (
                SELECT * FROM github_builds
                UNION ALL
                SELECT * FROM upload_builds
            )
            SELECT
                -- build
                b.id as build_id,
                b.build_number as build_number,
                b.restart_counter as build_restart_counter,
                -- project
                p.id as project_id,
                p.name as project_name,
                p.type as project_type,
                -- commit
                c.id as commit_id,
                c.message as commit_message,
                c.author_name as commit_author_name,
                c.author_email as commit_author_email,
                c.author_username as commit_author_email,
                c.committer_name as commit_committer_name,
                c.committer_email as commit_committer_email,
                c.committer_username as commit_committer_username,
                u.avatar_url as commit_committer_avatar_url,
                c.url as commit_url,
                c.branch as commit_branch,
                c.tag as commit_tag,
                -- source_upload
                su.filename as source_upload_filename,
                su.filesize as source_upload_filesize,
                -- job
                j.id as job_id,
                j.state as job_state,
                j.start_date::text as job_start_date,
                j.type as job_type,
                j.end_date::text as job_end_date,
                j.name as job_name,
                j.dependencies as job_dependencies,
                j.created_at::text as job_created_at,
                j.message as job_message,
                j.definition as job_definition,
                j.cluster_name as job_cluster_name,
                j.node_name as job_node_name,
                j.avg_cpu as job_avg_cpu,
                j.restarted as job_restarted,
                -- pull_request
                pr.title as pull_request_title,
                pr.url as pull_request_url
                FROM builds b
                INNER JOIN job j
                ON b.id = j.build_id
                INNER JOIN project p
                ON j.project_id = p.id
                LEFT OUTER JOIN commit c
                ON b.commit_id = c.id
                LEFT OUTER JOIN source_upload su
                ON b.source_upload_id = su.id
                LEFT OUTER JOIN "user" u
                ON c.committer_username = u.username
                LEFT OUTER JOIN pull_request pr
                ON c.pull_request_id = pr.id
                WHERE j.project_id = %(pid)s
                AND b.project_id = %(pid)s
                ORDER BY j.created_at DESC
        ''', {'pid': project_id})

        result = []
        for j in jobs:
            o = {
                'build': {
                    'id': j['build_id'],
                    'build_number': j['build_number'],
                    'restart_counter': j['build_restart_counter']
                },
                'project': {
                    'id': j['project_id'],
                    'name': j['project_name'],
                    'type': j['project_type']
                },
                'commit': None,
                'pull_request': None,
                'source_upload': None,
                'job': {
                    'id': j['job_id'],
                    'state': j['job_state'],
                    'start_date': j['job_start_date'],
                    'end_date': j['job_end_date'],
                    'name': j['job_name'],
                    'dependencies': j['job_dependencies'],
                    'created_at': j['job_created_at'],
                    'message': j['job_message'],
                    'definition': j['job_definition'],
                    'node_name': j['job_node_name'],
                    'avg_cpu': j['job_avg_cpu'],
                    'cluster_name': j['job_cluster_name'],
                    'restarted': j['job_restarted']
                }
            }

            if j['pull_request_title']:
                pr = {
                    'title': j['pull_request_title'],
                    'url': j['pull_request_url']
                }

                o['pull_request'] = pr

            if j['commit_id']:
                commit = {
                    'id': j['commit_id'],
                    'message': j['commit_message'],
                    'author_name': j['commit_author_name'],
                    'author_email': j['commit_author_email'],
                    'author_username': j['commit_author_email'],
                    'committer_name': j['commit_committer_name'],
                    'committer_email': j['commit_committer_email'],
                    'committer_username': j['commit_committer_username'],
                    'committer_avatar_url': j['commit_committer_avatar_url'],
                    'url': j['commit_url'],
                    'branch': j['commit_branch'],
                    'tag': j['commit_tag']
                }

                o['commit'] = commit

            if j['source_upload_filename']:
                up = {
                    'filename': j['source_upload_filename'],
                    'filesize': j['source_upload_filesize']
                }

                o['source_upload'] = up

            result.append(o)

        return result


@ns.route('/<job_id>/restart')
@api.response(403, 'Not Authorized')
class JobRestart(Resource):

    @api.response(200, 'Success', response_model)
    def get(self, project_id, job_id):
        '''
        Restart job
        '''
        user_id = g.token['user']['id']

        job = g.db.execute_one_dict('''
            SELECT state, type, build_id, restarted
            FROM job
            WHERE id = %s
            AND project_id = %s
        ''', [job_id, project_id])

        if not job:
            abort(404)

        job_type = job['type']
        job_state = job['state']
        build_id = job['build_id']
        restarted = job['restarted']

        if job_type not in ('run_project_container', 'run_docker_compose'):
            abort(400, 'Job type cannot be restarted')

        restart_states = ('error', 'failure', 'finished', 'killed', 'unstable')

        if job_state not in restart_states:
            abort(400, 'Job in state %s cannot be restarted' % job_state)

        if restarted:
            abort(400, 'This job has been already restarted')

        jobs = g.db.execute_many_dict('''
            SELECT state, id, dependencies
            FROM job
            WHERE build_id = %s
            AND project_id = %s
        ''', [build_id, project_id])

        restart_jobs = [job_id]

        while True:
            found = False
            for j in jobs:
                if j['id'] in restart_jobs:
                    continue

                if not j['dependencies']:
                    continue

                for dep in j['dependencies']:
                    dep_id = dep['job-id']

                    if dep_id in restart_jobs:
                        found = True
                        restart_jobs.append(j['id'])
                        break

            if not found:
                break

        for j in jobs:
            if j['id'] not in restart_jobs:
                continue

            if j['state'] not in restart_states and j['state'] not in ('skipped', 'queued'):
                abort(400, 'Some children jobs are still running')

        result = g.db.execute_one_dict('''
            SELECT username
            FROM "user"
            WHERE id = %s
        ''', [user_id])
        username = result['username']
        msg = 'Job restarted by %s\n' % username

        # Clone Jobs and adjust dependencies
        jobs = []
        for j in restart_jobs:
            jobs += g.db.execute_many_dict('''
                SELECT id, build_id, type, dockerfile, name, project_id, dependencies, repo, env_var, env_var_ref, build_arg, deployment, definition
                FROM job
                WHERE id = %s;
            ''', [j])

        name_job = {}
        for j in jobs:
            # Mark old jobs a restarted
            g.db.execute('''
                UPDATE job
                SET restarted = true
                WHERE id = %s;
            ''', [j['id']])

            # Create new ID for the new jobs
            j['id'] = str(uuid.uuid4())
            name_job[j['name']] = j

            m = re.search('(.*)\.([0-9]+)', j['name'])
            if m:
                # was already restarted
                c = int(m.group(2))
                j['name'] = '%s.%s' % (m.group(1), c+1)
            else:
                # First restart
                j['name'] = j['name'] + '.1'

        for j in jobs:
            for dep in j['dependencies']:
                if dep['job'] in name_job:
                    dep['job-id'] = name_job[dep['job']]['id']
                    dep['job'] = name_job[dep['job']]['name']

        for j in jobs:
            g.db.execute('''
                INSERT INTO job (state, id, build_id, type, dockerfile, name, project_id, dependencies, repo,
                                 env_var, env_var_ref, build_arg, deployment, definition, restarted)
                VALUES ('queued', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, false);
                INSERT INTO console (job_id, output)
                VALUES (%s, %s);
            ''', [j['id'],
                  j['build_id'],
                  j['type'],
                  j['dockerfile'],
                  j['name'],
                  j['project_id'],
                  json.dumps(j['dependencies']),
                  json.dumps(j['repo']),
                  json.dumps(j['env_var']),
                  json.dumps(j['env_var_ref']),
                  json.dumps(j['build_arg']),
                  json.dumps(j['deployment']),
                  json.dumps(j['definition']),
                  j['id'],
                  msg])
        g.db.commit()

        return OK('Successfully restarted job')

@ns.route('/<job_id>/abort')
@api.response(403, 'Not Authorized')
class JobAbort(Resource):

    @api.response(200, 'Success', response_model)
    #pylint: disable=unused-argument
    def get(self, project_id, job_id):
        '''
        Abort job
        '''
        g.db.execute('''
            INSERT INTO abort(job_id, user_id) VALUES(%s, %s)
        ''', [job_id, g.token['user']['id']])
        g.db.commit()

        return OK('Successfully aborted job')

@ns.route('/<job_id>/tabs', doc=False)
@api.response(403, 'Not Authorized')
class Tabs(Resource):

    def get(self, project_id, job_id):
        result = g.db.execute_many_dict('''
            SELECT name, data, type
            FROM job_markup
            WHERE   job_id = %s
                AND project_id = %s
        ''', [job_id, project_id])

        return result

@ns.route('/<job_id>/archive/download', doc=False)
@api.response(403, 'Not Authorized')
class ArchiveDownload(Resource):

    def get(self, project_id, job_id):
        filename = request.args.get('filename', None)

        if not filename:
            abort(404)

        result = g.db.execute_one_dict('''
            SELECT cluster_name
            FROM job
            WHERE   id = %s
                AND project_id = %s
        ''', [job_id, project_id])

        if not result or not result['cluster_name']:
            abort(404)

        job_cluster = result['cluster_name']
        key = '%s/%s' % (job_id, filename)

        if os.environ['INFRABOX_CLUSTER_NAME'] == job_cluster:
            f = storage.download_archive(key)
        else:
            c = g.db.execute_one_dict('''
                SELECT *
                FROM cluster
                WHERE name=%s
            ''', [job_cluster])
            url = '%s/api/v1/projects/%s/jobs/%s/archive/download?filename=%s' % (c['root_url'], project_id, job_id, filename)
            try:
                token = encode_user_token(g.token['user']['id'])
            except Exception:
                #public project has no token here.
                token = ""
            headers = {'Authorization': 'bearer ' + token}

            # TODO(ib-steffen): allow custom ca bundles
            r = requests.get(url, headers=headers, timeout=120, verify=False)
            f = BytesIO(r.content)
            f.seek(0)

        if not f:
            logger.error(key)
            abort(404)

        return send_file(f, as_attachment=True, attachment_filename=os.path.basename(filename))

@ns.route('/<job_id>/archive')
@api.response(403, 'Not Authorized')
class Archive(Resource):

    def get(self, project_id, job_id):
        '''
        Returns archive
        '''
        result = g.db.execute_one_dict('''
            SELECT archive
            FROM job
            WHERE   id = %s
                AND project_id = %s
        ''', [job_id, project_id])

        if not result or not result['archive']:
            return []

        return result['archive']


@ns.route('/<job_id>/console')
@api.response(403, 'Not Authorized')
class Console(Resource):

    def get(self, project_id, job_id):
        '''
        Returns job's console output
        '''
        result = g.db.execute_one_dict('''
            SELECT console
            FROM job
            WHERE   id = %s
                AND project_id = %s
        ''', [job_id, project_id])

        if result and result['console']:
            return Response(result['console'], mimetype='text/plain')

        result = g.db.execute_many_dict('''
            SELECT output
            FROM console
            WHERE job_id = %s
            ORDER BY date
        ''', [job_id])

        if not result:
            return ''

        output = ''
        for r in result:
            output += r['output']

        return Response(output, mimetype='text/plain')


@ns.route('/<job_id>/output', doc=False)
@api.response(403, 'Not Authorized')
class Output(Resource):

    #pylint: disable=unused-argument
    def get(self, project_id, job_id):
        g.release_db()

        key = '%s.tar.gz' % job_id
        f = storage.download_output(key)

        if not f:
            abort(404)

        return send_file(f, attachment_filename=key)

@ns.route('/<job_id>/testruns', doc=False)
@api.response(403, 'Not Authorized')
class Testruns(Resource):

    def get(self, project_id, job_id):
        '''
        Returns test runs
        '''
        result = g.db.execute_many_dict('''
            SELECT tr.state, tr.name, tr.suite, tr.duration, tr.message, tr.stack, to_char(tr.timestamp, 'YYYY-MM-DD HH24:MI:SS') as timestamp
            FROM test_run tr
            WHERE job_id = %s
            AND project_id = %s
        ''', [job_id, project_id])

        return result

@ns.route('/<job_id>/tests/history', doc=False)
@api.response(403, 'Not Authorized')
class TestHistory(Resource):

    def get(self, project_id, job_id):

        test = request.args.get('test', None)
        suite = request.args.get('suite', None)

        if not test or not suite:
            abort(404)

        results = g.db.execute_many_dict('''
	    SELECT
		b.build_number,
		tr.duration duration,
		tr.state state,
		m.name measurement_name,
		m.value measurement_value,
		m.unit measurement_unit
	    FROM test_run tr
	    INNER JOIN job j
		ON j.id = tr.job_id
		AND j.name = (SELECT name FROM job WHERE id = %s)
		AND j.project_id = tr.project_id
	    INNER JOIN build b
		ON b.id = j.build_id
		AND b.project_id = j.project_id
	    LEFT OUTER JOIN measurement m
		ON tr.id = m.test_run_id
		AND m.project_id = b.project_id
	    WHERE   tr.name = %s
		AND tr.suite = %s
		AND tr.project_id = %s
	    ORDER BY b.build_number, b.restart_counter
	    LIMIT 30
        ''', [job_id, test, suite, project_id])

        current_build = None
        result = []

        for r in results:
            if current_build:
                if current_build['build_number'] != r['build_number']:
                    result.append(current_build)
                    current_build = None

            if not current_build:
                current_build = {
                    'build_number': r['build_number'],
                    'duration': r['duration'],
                    'state': r['state'],
                    'measurements': []
                }

            if r['measurement_name']:
                current_build['measurements'].append({
                    'name': r['measurement_name'],
                    'unit': r['measurement_unit'],
                    'value': r['measurement_value']
                })

        if current_build:
            result.append(current_build)

        return result

badge_model = api.model('Badge', {
    'subject': fields.String,
    'status': fields.String,
    'color': fields.String,
})

@ns.route('/<job_id>/badges')
@api.response(403, 'Not Authorized')
class Badges(Resource):

    @api.marshal_list_with(badge_model)
    def get(self, project_id, job_id):
        '''
        Returns job's badges
        '''
        result = g.db.execute_many_dict('''
            SELECT subject, status, color
            FROM job_badge
            WHERE   job_id = %s
                AND project_id = %s
        ''', [job_id, project_id])

        return result

def compact(s):
    c = int(len(s) / 100)

    if c <= 1:
        return s

    result = []

    while True:
        if not s:
            break

        r = {
            'mem': 0.0,
            'cpu': 0.0,
            'date': 0
        }

        count = 1
        for count in range(1, c + 1):
            if not s:
                break

            l = s.pop()
            r['mem'] += l['mem']
            r['cpu'] += l['cpu']
            r['date'] += l['date']


        r['mem'] = r['mem'] / count
        r['cpu'] = r['cpu'] / count
        r['date'] = r['date'] / count
        result.append(r)

    return result

@ns.route('/<job_id>/stats', doc=False)
@api.response(403, 'Not Authorized')
class Stats(Resource):

    def get(self, project_id, job_id):
        result = g.db.execute_one_dict('''
            SELECT stats
            FROM job
            WHERE   id = %s
                AND project_id = %s
        ''', [job_id, project_id])

        if not result:
            abort(404)

        if not result['stats']:
            return {}

        stats = json.loads(result['stats'])

        r = {}
        for j in stats:
            r[j] = compact(stats[j])

        return r

@ns.route('/<job_id>/cache/clear')
@api.response(200, 'Success', response_model)
@api.response(403, 'Not Authorized')
class JobCacheClear(Resource):

    def get(self, project_id, job_id):
        '''
        Clear job's cache
        '''
        job = g.db.execute_one_dict('''
            SELECT j.name, branch from job j
            INNER JOIN build b
                ON b.id = j.build_id
                AND j.project_id = b.project_id
            LEFT OUTER JOIN "commit" c
                ON b.commit_id = c.id
                AND c.project_id = b.project_id
            WHERE
                j.id = %s AND
                j.project_id = %s
        ''', [job_id, project_id])

        if not job:
            abort(404)

        key = 'project_%s_job_%s.tar.snappy' % (project_id, job['name'])
        storage.delete_cache(key)

        return OK('Cleared cache')
