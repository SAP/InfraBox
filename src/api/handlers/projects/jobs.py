import json
import os
import uuid
import re
import mimetypes

from io import BytesIO

import requests

from flask import g, abort, Response, send_file, request, redirect
from flask_restx import Resource, fields

from pyinfraboxutils import get_logger
from pyinfraboxutils.ibflask import OK
from pyinfraboxutils.ibrestplus import api, response_model
from pyinfraboxutils.storage import storage
from pyinfraboxutils.token import encode_user_token

logger = get_logger('api')

mimetypes.init()
mimetypes.add_type("text/plain", ".log")

ns = api.namespace('Jobs',
                   path='/api/v1/projects/<project_id>/jobs/',
                   description='Commit related operations')


@ns.route('/', doc=False)
@api.response(403, 'Not Authorized')
class Jobs(Resource):

    def get(self, project_id):
        build_from = request.args.get('from', None)
        build_to = request.args.get('to', None)
        sha = request.args.get('sha', None)
        branch = request.args.get('branch', None)
        cronjob = request.args.get('cronjob', None)
        state = request.args.get('state', None)
        build_limit = request.args.get('build_limit', None)

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
        if not build_limit:
            if build_from == 0:
                build_limit = 10
            else:
                build_limit = build_to - build_from
        else:
            try:
                build_limit = int(build_limit)
            except:
                build_limit = 10

        build_limit = min(50, build_limit)

        #if build_to - build_from > 200:
        #    build_from = build_to - 200

        # we can avoid join with job table if there is no filter on state
        if state:
            sql_stmt = '''
                SELECT DISTINCT b.id, build_number, restart_counter
                FROM build b
                INNER JOIN job j
                ON b.id = j.build_id
                LEFT OUTER JOIN commit c
                ON b.commit_id = c.id
                WHERE b.project_id = %(pid)s
                AND b.build_number < %(to)s
                AND b.build_number >= %(from)s
                AND (%(sha)s IS NULL OR c.id = %(sha)s)
                AND (%(branch)s IS NULL OR c.branch = %(branch)s)
                AND (%(cronjob)s IS NULL OR b.is_cronjob = %(cronjob)s)
                AND (%(state)s IS NULL OR j.state = %(state)s)
                ORDER BY build_number DESC, restart_counter DESC
                LIMIT %(build_limit)s
            '''
        else:
            sql_stmt = '''
                SELECT DISTINCT b.id, build_number, restart_counter
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
                LIMIT %(build_limit)s
            '''

        p = g.db.execute_many(sql_stmt, {
            'pid': project_id,
            'from': build_from,
            'to': build_to,
            'sha': sha,
            'branch': branch,
            'cronjob': cronjob,
            'build_limit': build_limit,
            'state': state,
        })

        build_ids = tuple(x[0] for x in p)

        if not build_ids:
            return []

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
                WHERE b.id IN %(build_ids)s
                ORDER BY j.created_at DESC
        ''', {
            'build_ids': build_ids
        })

        result = []
        for j in jobs:
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
        user_id = None
        if g.token['type'] == 'user':
            user_id = g.token['user']['id']
        elif g.token['type'] == 'project':
            if g.token['project']['id'] != project_id:
                abort(400, "invalid project token")

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
            SELECT state, id, dependencies, restarted
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

                #Avoid generating duplicate jobs. Fix #227(https://github.com/SAP/InfraBox/issues/227)
                if j['restarted']:
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

        if user_id is not None:
            result = g.db.execute_one_dict('''
                SELECT username
                FROM "user"
                WHERE id = %s
            ''', [user_id])
            username_or_token = result['username']
        else:
            result = g.db.execute_one_dict('''
                                SELECT description
                                FROM auth_token
                                WHERE id = %s
                            ''', [g.token['id']])
            username_or_token = "project token " + result['description']
        msg = 'Job restarted by %s\n' % username_or_token

        # Clone Jobs and adjust dependencies
        jobs = []
        for j in restart_jobs:
            jobs += g.db.execute_many_dict('''
                SELECT id, build_id, type, dockerfile, name, project_id, dependencies,
                       repo, env_var, env_var_ref, build_arg, deployment, definition, cluster_name
                FROM job
                WHERE id = %s;
            ''', [j])

        old_id_job = {}
        for j in jobs:
            # Mark old jobs a restarted
            g.db.execute('''
                UPDATE job
                SET restarted = true
                WHERE id = %s;
            ''', [j['id']])

            # Create new ID for the new jobs
            old_id_job[j['id']] = j
            j['id'] = str(uuid.uuid4())

            job_name_items = j['name'].split('/')
            last_item = job_name_items[-1]
            m = re.search('(.*)\.([0-9]+)', last_item)
            if m:
                # was already restarted
                c = int(m.group(2))
                front = '/'.join(job_name_items[0:-1])
                if front:
                    j['name'] = front + '/' + '%s.%s' % (m.group(1), c + 1)
                else:
                    j['name'] = '%s.%s' % (m.group(1), c + 1)
            else:
                # First restart
                j['name'] = j['name'] + '.1'

        for j in jobs:
            for dep in j['dependencies']:
                if dep['job-id'] in old_id_job:
                    dep['job'] = old_id_job[dep['job-id']]['name']
                    dep['job-id'] = old_id_job[dep['job-id']]['id']

        for j in jobs:
            g.db.execute('''
                INSERT INTO job (state, id, build_id, type, dockerfile, name, project_id, dependencies, repo,
                                 env_var, env_var_ref, build_arg, deployment, definition, restarted, cluster_name)
                VALUES ('queued', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, false, %s);
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
                  j['cluster_name'],
                  j['id'],
                  msg])
        g.db.commit()

        return OK('Successfully restarted job')

@ns.route('/<job_id>/rerun')
@api.response(403, 'Not Authorized')
class JobRerun(Resource):

    @api.response(200, 'Success', response_model)
    def get(self, project_id, job_id):
        '''
        Rerun a single job without running jobs depend on it
        '''
        # restart single job only
        # request like:
        # https://infrabox.datahub.only.sap/api/v1/projects/{PROJECT_ID}/jobs/{INFRABOX_JOB_ID}/rerun

        user_id = None
        if g.token['type'] == 'user':
            user_id = g.token['user']['id']
        elif g.token['type'] == 'project':
            if g.token['project']['id'] != project_id:
                abort(400, "invalid project token")

        logger.debug('Prepare to rerun job %s of project %s' % (job_id, project_id))
        job = g.db.execute_one_dict('''
            SELECT state, type, build_id, restarted, dependencies, name
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

        # while the parent job is in running state, skip rerun current job
        parent_jobs = job['dependencies']
        for j in parent_jobs:
            j_id = j['job-id']
            p_job = g.db.execute_one_dict('''
            SELECT state, type, build_id, restarted
            FROM job
            WHERE id = %s
            AND project_id = %s
            ''', [j_id, project_id])
            if not p_job:
                abort(404)
            if p_job['state'] in ['queued','running']:
                abort(400, 'Job %s(%s) has executing parent job' % (job_id, job['name']))
        # while the parent job is in running state, skip rerun current job

        jobs = g.db.execute_many_dict('''
            SELECT state, id, dependencies, restarted
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

                if j['restarted']:
                    continue

                for dep in j['dependencies']:
                    dep_id = dep['job-id']

                    if dep_id in restart_jobs:
                        found = True
                        restart_jobs.append(j['id'])
                        break

            if not found:
                break

        # get all jobs, filter the jobs marked to be restarted, check the status is running or not
        for j in jobs:
            if j['id'] not in restart_jobs:
                continue

            if j['state'] not in restart_states and j['state'] not in ('skipped', 'queued'):
                abort(400, 'Some children jobs are still running')

        # print mssage for the restart operator
        if user_id is not None:
            result = g.db.execute_one_dict('''
                SELECT username
                FROM "user"
                WHERE id = %s
            ''', [user_id])
            username_or_token = result['username']
        else:
            result = g.db.execute_one_dict('''
                                SELECT description
                                FROM auth_token
                                WHERE id = %s
                            ''', [g.token['id']])
            username_or_token = "project token " + result['description']
        msg = 'Job restarted by %s\n' % username_or_token

        # Clone Jobs and adjust dependencies
        # get jobs that marked as restart from table job
        jobs = []
        for j in restart_jobs:
            jobs += g.db.execute_many_dict('''
                SELECT id, build_id, type, dockerfile, name, project_id, dependencies,
                       repo, env_var, env_var_ref, build_arg, deployment, definition, cluster_name
                FROM job
                WHERE id = %s;
            ''', [j])
        logger.debug('## get jobs that marked as restart from table job:')
        logger.debug(str(jobs))

        # get job thet restart it self only.
        single_job = []
        single_job += g.db.execute_many_dict('''
            SELECT id, build_id, type, dockerfile, name, project_id, dependencies,
                    repo, env_var, env_var_ref, build_arg, deployment, definition, cluster_name
            FROM job
            WHERE id = %s;
        ''', [job_id])

        old_id_job = {}
        for j in single_job:
            # Mark old jobs a restarted
            g.db.execute('''
                UPDATE job
                SET restarted = true
                WHERE id = %s;
            ''', [j['id']])

            # Create new ID for the new jobs
            old_id_job[j['id']] = j
            j['id'] = str(uuid.uuid4())

            job_name_items = j['name'].split('/')
            last_item = job_name_items[-1]
            m = re.search('(.*)\.([0-9]+)', last_item)
            if m:
                # was already restarted
                c = int(m.group(2))
                front = '/'.join(job_name_items[0:-1])
                if front:
                    j['name'] = front + '/' + '%s.%s' % (m.group(1), c + 1)
                else:
                    j['name'] = '%s.%s' % (m.group(1), c + 1)
            else:
                # First restart
                j['name'] = j['name'] + '.1'

            logger.debug('new jod id: %s, new job name: %s' % (j['id'], j['name']))

        for j in jobs:
            for dep in j['dependencies']:
                if dep['job-id'] in old_id_job:
                    dep['job'] = old_id_job[dep['job-id']]['name']
                    dep['job-id'] = old_id_job[dep['job-id']]['id']
            logger.debug('## dep in jobs:')
            logger.debug(str(dep))

        for j in single_job:
            g.db.execute('''
                INSERT INTO job (state, id, build_id, type, dockerfile, name, project_id, dependencies, repo,
                                 env_var, env_var_ref, build_arg, deployment, definition, restarted, cluster_name)
                VALUES ('queued', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, false, %s);
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
                  j['cluster_name'],
                  j['id'],
                  msg])
        g.db.commit()

        for j in jobs:
            if j['id'] not in [job_id]:
                g.db.execute('''
                    UPDATE job 
                    SET dependencies = %s 
                    WHERE id = %s;
                ''', [
                    json.dumps(j['dependencies']),
                    j['id']
                ])
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
        force_download = request.args.get('view', "false") == "false"
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

        f = storage.download_archive(key)
        if not f and os.environ['INFRABOX_CLUSTER_NAME'] != job_cluster:
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
            abort(404)

        filename = os.path.basename(filename)

        return send_file(f, as_attachment=force_download, attachment_filename=filename,\
                         mimetype=mimetypes.guess_type(filename)[0])

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


@ns.route('/<job_id>/archive/download/all')
@api.response(403, 'Not Authorized')
class ArchiveDownloadAll(Resource):

    def get(self, project_id, job_id):
        '''
        Returns all archives
        '''
        return redirect("/api/v1/projects/%s/jobs/%s/archive/download?filename=all_archives.tar.gz" %(project_id, job_id))

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

        j = g.db.execute_one_dict("""
            SELECT id FROM job
            WHERE id = %s
                AND project_id = %s
        """, [job_id, project_id])

        if not j:
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
	    INNER JOIN build b
		ON b.id = j.build_id
	    LEFT OUTER JOIN measurement m
		ON tr.id = m.test_run_id
		AND m.project_id = b.project_id
	    WHERE   tr.name = %s
		AND tr.suite = %s
		AND tr.project_id = %s
	    ORDER BY b.build_number, b.restart_counter
	    LIMIT 30
        ''', [test, suite, project_id])

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
            l = s.pop(0)
            r['mem'] += l['mem']
            r['cpu'] += l['cpu']
            r['date'] += l['date']

            if not s:
                break

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
