import json

from flask import g, abort, Response, send_file
from flask_restplus import Resource

from pyinfraboxutils.ibflask import auth_required, OK
from pyinfraboxutils.storage import storage

from dashboard_api.namespaces import project as ns

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
                j.start_date as job_start_date,
                j.type as job_type,
                j.end_date as job_end_date,
                j.name as job_name,
                j.cpu as job_cpu,
                j.memory as job_memory,
                j.dependencies as job_dependencies,
                j.created_at as job_created_at,
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
                    'start_date': str(j['job_start_date']),
                    'end_date': str(j['job_end_date']),
                    'name': j['job_name'],
                    'cpu': j['job_cpu'],
                    'memory': j['job_memory'],
                    'dependencies': j['job_dependencies'],
                    'created_at': str(j['job_created_at'])
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
            SELECT state, type
            FROM job
            WHERE id = %s
            AND project_id = %s
        ''', [job_id, project_id])

        if not job:
            abort(404)

        job_type = job['type']
        job_state = job['state']

        if job_type not in ('run_project_container', 'run_docker_compose'):
            abort(400, 'Job type cannot be restarted')

        if job_state not in ('error', 'failure', 'finished', 'killed'):
            abort(400, 'Job in state %s cannot be restarted' % job_state)

        g.db.execute('''
            UPDATE job SET state = 'queued', console = null WHERE id = %s
        ''', [job_id])
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

        if not result:
            return ''

        if not result['console']:
            return ''

        return Response(result['console'], mimetype='text/plain')

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
            SELECT tr.state, t.name, t.suite, tr.duration, t.build_number, tr.message, tr.stack
            FROM test t
            INNER JOIN test_run tr
                ON t.id = tr.test_id
                AND t.project_id = %s
                AND tr.project_id = %s
                AND tr.job_id = %s
        ''', [project_id, project_id, job_id])

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
