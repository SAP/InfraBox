import json
import os

import requests

from flask import g, abort, Response, send_file, request
from flask_restplus import Resource

from pyinfraboxutils import get_logger
from pyinfraboxutils.ibflask import auth_required, OK
from pyinfraboxutils.storage import storage
from api.namespaces import project as ns
from pyinfraboxutils.token import encode_user_token

logger = get_logger('api')

@ns.route('/<project_id>/jobs/')
class Jobs(Resource):

    @auth_required(['user'], allow_if_public=True)
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
                j.cpu as job_cpu,
                j.memory as job_memory,
                j.dependencies as job_dependencies,
                j.created_at::text as job_created_at,
                j.message as job_message,
                j.definition as job_definition,
                j.node_name as job_node_name,
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
                    'cpu': j['job_cpu'],
                    'memory': j['job_memory'],
                    'dependencies': j['job_dependencies'],
                    'created_at': j['job_created_at'],
                    'message': j['job_message'],
                    'definition': j['job_definition'],
                    'node_name': j['job_node_name'],
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


@ns.route('/<project_id>/jobs/<job_id>/restart')
class JobRestart(Resource):

    @auth_required(['user'])
    def get(self, project_id, job_id):

        job = g.db.execute_one_dict('''
            SELECT state, type, build_id
            FROM job
            WHERE id = %s
            AND project_id = %s
        ''', [job_id, project_id])

        if not job:
            abort(404)

        job_type = job['type']
        job_state = job['state']
        build_id = job['build_id']

        if job_type not in ('run_project_container', 'run_docker_compose'):
            abort(400, 'Job type cannot be restarted')

        restart_states = ('error', 'failure', 'finished', 'killed')

        if job_state not in restart_states:
            abort(400, 'Job in state %s cannot be restarted' % job_state)

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

            if j['state'] not in restart_states and j['state'] != 'skipped':
                abort(400, 'Some children jobs are still running')

        for j in restart_jobs:
            g.db.execute('''
                UPDATE job
                SET state = 'queued', console = null, message = null
                WHERE id = %s
            ''', [j])
        g.db.commit()

        return OK('Successfully restarted job')

@ns.route('/<project_id>/jobs/<job_id>/abort')
class JobAbort(Resource):

    @auth_required(['user'])
    #pylint: disable=unused-argument
    def get(self, project_id, job_id):
        g.db.execute('''
            INSERT INTO abort(job_id) VALUES(%s)
        ''', [job_id])
        g.db.commit()

        return OK('Successfully aborted job')

@ns.route('/<project_id>/jobs/<job_id>/testresults')
class Testresults(Resource):

    @auth_required(['user'], allow_if_public=True)
    def get(self, project_id, job_id):
        result = g.db.execute_many_dict('''
            SELECT tr.state, t.name, t.suite, tr.duration, t.build_number, tr.message, tr.stack
            FROM test t
            INNER JOIN test_run tr
                ON t.id = tr.test_id
                AND t.project_id = tr.project_id
            WHERE   tr.project_id = %s
                AND tr.job_id = %s
        ''', [project_id, job_id])

        return result

@ns.route('/<project_id>/jobs/<job_id>/tabs')
class Tabs(Resource):

    @auth_required(['user'], allow_if_public=True)
    def get(self, project_id, job_id):
        result = g.db.execute_many_dict('''
            SELECT name, data, type
            FROM job_markup
            WHERE   job_id = %s
                AND project_id = %s
        ''', [job_id, project_id])

        return result

@ns.route('/<project_id>/jobs/<job_id>/archive/download')
class ArchiveDownload(Resource):

    @auth_required(['user'], allow_if_public=True)
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
            except AttributeError:
                #public project has no token here.
                token = ""
            headers = {'Authorization': 'bearer ' + token}
            logger.info('get archive %s from %s', [filename, url])

            # TODO(ib-steffen): allow custom ca bundles
            r = requests.get(url,headers=headers, timeout=120, verify=False, stream=True)
            f = r.raw

        if not f:
            logger.error(key)
            abort(404)

        return send_file(f, as_attachment=True, attachment_filename=os.path.basename(filename))

@ns.route('/<project_id>/jobs/<job_id>/archive')
class Archive(Resource):

    @auth_required(['user'], allow_if_public=True)
    def get(self, project_id, job_id):
        result = g.db.execute_one_dict('''
            SELECT archive
            FROM job
            WHERE   id = %s
                AND project_id = %s
        ''', [job_id, project_id])

        if not result or not result['archive']:
            return []

        return result['archive']


@ns.route('/<project_id>/jobs/<job_id>/console')
class Console(Resource):

    @auth_required(['user'], allow_if_public=True)
    def get(self, project_id, job_id):
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


@ns.route('/<project_id>/jobs/<job_id>/output')
class Output(Resource):

    @auth_required(['user'], allow_if_public=True)
    #pylint: disable=unused-argument
    def get(self, project_id, job_id):
        g.release_db()

        key = '%s.tar.gz' % job_id
        f = storage.download_output(key)

        if not f:
            abort(404)

        return send_file(f, attachment_filename=key)

@ns.route('/<project_id>/jobs/<job_id>/testruns')
class Testruns(Resource):

    @auth_required(['user'], allow_if_public=True)
    def get(self, project_id, job_id):
        result = g.db.execute_many_dict('''
            SELECT tr.state, t.name, t.suite, tr.duration, t.build_number, tr.message, tr.stack, to_char(tr.timestamp, 'YYYY-MM-DD HH24:MI:SS') as timestamp
            FROM test t
            INNER JOIN test_run tr
                ON t.id = tr.test_id
                AND t.project_id = %s
                AND tr.project_id = %s
                AND tr.job_id = %s
        ''', [project_id, project_id, job_id])

        return result

@ns.route('/<project_id>/jobs/<job_id>/tests/history')
class TestHistory(Resource):

    @auth_required(['user'], allow_if_public=True)
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
	    FROM test t
	    INNER JOIN test_run tr
		ON t.id = tr.test_id
		AND tr.project_id = t.project_id
	    INNER JOIN job j
		ON j.id = tr.job_id
		AND j.name = (SELECT name FROM job WHERE id = %s)
		AND j.project_id = t.project_id
	    INNER JOIN build b
		ON b.id = j.build_id
		AND b.project_id = j.project_id
	    LEFT OUTER JOIN measurement m
		ON tr.id = m.test_run_id
		AND m.project_id = b.project_id
	    WHERE   t.name = %s
		AND t.suite = %s
		AND t.project_id = %s
	    ORDER BY b.build_number, b.restart_counter
	    LIMIT 30
        ''', [job_id, test, suite, project_id])

        current_build = None
        result = []

        for r in results:
            if current_build and current_build['build_number'] != r['build_number']:
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


@ns.route('/<project_id>/jobs/<job_id>/badges')
class Badges(Resource):

    @auth_required(['user'], allow_if_public=True)
    def get(self, project_id, job_id):
        result = g.db.execute_many_dict('''
            SELECT subject, status, color
            FROM job_badge
            WHERE   job_id = %s
                AND project_id = %s
        ''', [job_id, project_id])

        return result

@ns.route('/<project_id>/jobs/<job_id>/stats')
class Stats(Resource):

    @auth_required(['user'], allow_if_public=True)
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

        return json.loads(result['stats'])

@ns.route('/<project_id>/jobs/<job_id>/cache/clear')
class JobCacheClear(Resource):

    @auth_required(['user'])
    def get(self, project_id, job_id):
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

        key = 'project_%s_branch_%s_job_%s.tar.gz' % (project_id, job['branch'], job['name'])
        storage.delete_cache(key)

        return OK('Cleared cache')
