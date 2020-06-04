import json
import uuid

from flask import g, abort
from flask_restx import Resource

from pyinfraboxutils.ibrestplus import api, response_model
from pyinfraboxutils.ibflask import OK
from pyinfraboxutils.storage import storage

ns = api.namespace('Builds',
                   path='/api/v1/projects/<project_id>/builds',
                   description='Build related operations')


def restart_build(project_id, build_id):
    username_or_token = None

    if g.token['type'] == 'user':
        user_id = g.token['user']['id']

        build = g.db.execute_one_dict('''
            SELECT b.*
            FROM build b
            INNER JOIN collaborator co
                ON b.id = %s
                AND b.project_id = co.project_id
                AND co.project_id = %s
                AND co.user_id = %s
        ''', [build_id, project_id, user_id])

        result = g.db.execute_one_dict('''
            SELECT username
            FROM "user"
            WHERE id = %s
        ''', [user_id])
        username_or_token = result['username']
    else:
        if g.token['project']['id'] != project_id:
            abort(400)

        build = g.db.execute_one_dict('''
            SELECT *
            FROM build 
            WHERE id = %s
                AND project_id = %s
        ''', [build_id, project_id])

        result = g.db.execute_one_dict('''
                    SELECT description
                    FROM auth_token
                    WHERE id = %s
                ''', [g.token['id']])
        username_or_token = "project token " + result['description']

    if not build:
        abort(404)

    result = g.db.execute_one_dict('''
        SELECT max(restart_counter) as restart_counter
        FROM build
        WHERE build_number = %s
          AND project_id = %s
    ''', [build['build_number'], project_id])

    restart_counter = result['restart_counter'] + 1

    result = g.db.execute_one_dict('''
        INSERT INTO build (commit_id, build_number,
                           project_id, restart_counter, source_upload_id)
        VALUES (%s, %s, %s, %s, %s) RETURNING id
    ''', [build['commit_id'],
          build['build_number'],
          project_id,
          restart_counter,
          build['source_upload_id']])

    new_build_id = result['id']

    job = g.db.execute_one_dict('''
           SELECT repo, env_var, definition FROM job
           WHERE project_id = %s
           AND name = 'Create Jobs'
           AND build_id = %s
    ''', [project_id, build_id])

    env_var = job['env_var']
    if env_var:
        env_var = json.dumps(env_var)

    repo = job['repo']
    if repo:
        repo = json.dumps(repo)

    definition = job['definition']
    if definition:
        definition = json.dumps(definition)

    job_id = str(uuid.uuid4())
    msg = 'Build restarted by %s\n' % username_or_token
    g.db.execute('''
        INSERT INTO job (id, state, build_id, type,
            name, project_id, dockerfile, repo, env_var, definition, cluster_name)
        VALUES (%s, 'queued', %s, 'create_job_matrix',
                'Create Jobs', %s, '', %s, %s, %s, null);
        INSERT INTO console (job_id, output)
        VALUES (%s, %s);
    ''', [job_id, new_build_id, project_id, repo, env_var, definition, job_id, msg])
    g.db.commit()

    return OK('Restarted', {'build': {'id': new_build_id, 'restartCounter': restart_counter}})


@ns.route('/<build_id>/restart')
@api.response(403, 'Not Authorized')
class BuildRestart(Resource):

    @api.response(200, 'Success', response_model)
    def get(self, project_id, build_id):
        '''
        Restart build
        '''
        return restart_build(project_id, build_id)


@ns.route('/<build_id>/abort')
@api.response(403, 'Not Authorized')
class BuildAbort(Resource):

    @api.response(200, 'Success', response_model)
    def get(self, project_id, build_id):
        '''
        Abort build
        '''
        jobs = g.db.execute_many_dict('''
            SELECT id
            FROM job
            WHERE build_id = %s
              AND project_id = %s
        ''', [build_id, project_id])

        for j in jobs:
            g.db.execute('''
                INSERT INTO abort(job_id, user_id) VALUES(%s, %s)
            ''', [j['id'], g.token['user']['id']])

        g.db.commit()

        return OK('Aborted all jobs')

@ns.route('/<build_id>/cache/clear')
@api.response(403, 'Not Authorized')
class BuildCacheClear(Resource):

    @api.response(200, 'Success', response_model)
    def get(self, project_id, build_id):
        '''
        Clear cache of all jobs in build
        '''
        jobs = g.db.execute_many_dict('''
            SELECT j.name, branch from job j
            INNER JOIN build b
                ON b.id = j.build_id
                AND j.project_id = b.project_id
            LEFT OUTER JOIN "commit" c
                ON b.commit_id = c.id
                AND c.project_id = b.project_id
            WHERE
                b.id = %s AND
                j.project_id = %s
        ''', [build_id, project_id])

        for j in jobs:
            key = 'project_%s_job_%s.tar.snappy' % (project_id, j['name'])
            storage.delete_cache(key)

        return OK('Cleared cache')

@ns.route('/<build_number>/<build_restart_counter>', doc=False)
@api.response(403, 'Not Authorized')
class Build(Resource):

    def get(self, project_id, build_number, build_restart_counter):
        jobs = g.db.execute_many_dict('''
            SELECT
            -- build
            b.id as build_id,
            b.build_number as build_number,
            b.restart_counter as build_restart_counter,
            b.is_cronjob as build_is_cronjob,
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
            to_char(j.start_date, 'YYYY-MM-DD HH24:MI:SS') as job_start_date,
            j.type as job_type,
            to_char(j.end_date, 'YYYY-MM-DD HH24:MI:SS') as job_end_date,
            j.name as job_name,
            j.dependencies as job_dependencies,
            to_char(j.created_at, 'YYYY-MM-DD HH24:MI:SS') as job_created_at,
            j.message as job_message,
            j.definition as job_definition,
            j.node_name as job_node_name,
            j.avg_cpu as job_avg_cpu,
            j.restarted as job_restarted,
            -- pull_request
            pr.title as pull_request_title,
            pr.url as pull_request_url
        FROM build b
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
        WHERE   p.id = %s
            AND b.build_number = %s
            AND b.restart_counter = %s
        ''', [project_id, build_number, build_restart_counter])

        result = []
        for j in jobs:
            limits = {}
            if j['job_definition']:
                limits = j['job_definition'].get('resources', {}).get('limits', {})

            o = {
                'build': {
                    'id': j['build_id'],
                    'build_number': j['build_number'],
                    'restart_counter': j['build_restart_counter'],
                    'is_cronjob': j['build_is_cronjob']
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
                    'memory': limits.get('memory', 1024),
                    'cpu': limits.get('cpu', 1),
                    'dependencies': j['job_dependencies'],
                    'created_at': j['job_created_at'],
                    'message': j['job_message'],
                    'definition': j['job_definition'],
                    'node_name': j['job_node_name'],
                    'avg_cpu': j['job_avg_cpu'],
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
