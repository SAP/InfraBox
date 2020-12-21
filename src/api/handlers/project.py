import uuid
import urllib
import os
import json
import mimetypes

from datetime import datetime
from functools import wraps, update_wrapper

import requests

from flask import g, request, abort, make_response, Response, send_file
from flask_restx import Resource, fields

from werkzeug.datastructures import FileStorage

from pyinfraboxutils import get_logger, get_root_url

from pyinfraboxutils.ibflask import OK
from pyinfraboxutils.ibrestplus import api, response_model
from pyinfraboxutils.storage import storage
from pyinfraboxutils.token import encode_project_token

ns = api.namespace('Projects',
                   path='/api/v1/projects/<project_id>',
                   description='Project related operations')


logger = get_logger('api')

enable_upload_forward = False
if os.environ['INFRABOX_HA_ENABLED'] == 'true':
    enable_upload_forward = True
elif os.environ['INFRABOX_CLUSTER_NAME'] == 'master':
    enable_upload_forward = True

def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Surrogate-Control'] = 'no-store'
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, proxy-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.last_modified = datetime.now()
        response.add_etag()
        return response

    return update_wrapper(no_cache, view)

def get_badge(subject, status, color):
    subject = urllib.quote(subject)
    status = urllib.quote(status)
    color = urllib.quote(color)

    url = 'https://img.shields.io/static/v1.svg?label=%s&message=%s&color=%s' % (subject, status, color)

    resp = requests.get(url)

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]

    return Response(resp.content, resp.status_code, headers)

@ns.route('/state.svg')
@api.doc(security=[])
class State(Resource):

    @nocache
    def get(self, project_id):
        '''
        State badge
        '''
        p = g.db.execute_one_dict("""
            SELECT type FROM project WHERE id = %s
        """, [project_id])

        if not p:
            abort(404)

        project_type = p['type']

        build_number = request.args.get('build_number', None)
        build_restart_count = request.args.get('build_restart_counter', 1)

        rows = None
        if request.args.get('branch', None) and project_type in ('github', 'gerrit'):
            rows = g.db.execute_many_dict('''
                SELECT state FROM job j
                WHERE j.project_id = %s
                AND j.build_id = (
                    SELECT b.id
                    FROM build b
                    INNER JOIN "commit" c
                        ON c.id = b.commit_id
                        AND c.project_id = b.project_id
                    WHERE b.project_id = %s
                        AND c.branch = %s
                    ORDER BY build_number DESC, restart_counter DESC
                    LIMIT 1
                )
            ''', [project_id, project_id, request.args['branch']])
        elif build_number and build_restart_count:
            rows = g.db.execute_many_dict('''
                SELECT state FROM job j
                WHERE j.project_id = %s
                AND j.build_id = (
                    SELECT id
                    FROM build
                    WHERE project_id = %s
                    AND build_number = %s
                    AND restart_counter = %s
                )
            ''', [project_id, project_id, build_number, build_restart_count])
        else:
            rows = g.db.execute_many_dict('''
                SELECT state FROM job j
                WHERE j.project_id = %s
                AND j.build_id = (
                    SELECT id
                    FROM build
                    WHERE project_id = %s
                    ORDER BY build_number DESC, restart_counter DESC
                    LIMIT 1
                )
            ''', [project_id, project_id])

        if not rows:
            abort(404)

        status = 'finished'
        color = 'brightgreen'

        for r in rows:
            state = r['state']
            if state in ('running', 'queued', 'scheduled'):
                status = 'running'
                color = 'grey'
                break

            if state in ('failure', 'error', 'killed', 'unstable'):
                status = state
                color = 'red'

            if state == 'unstable':
                status = state
                color = 'yellow'

        return get_badge('infrabox', status, color)

@ns.route('/tests.svg')
@api.doc(security=[])
class Tests(Resource):

    @nocache
    def get(self, project_id):
        '''
        Tests badge
        '''
        branch = request.args.get('branch', None)
        job_name = request.args.get('job_name', '%')
        build_number = request.args.get('build_number', None)
        build_restart_count = request.args.get('build_restart_counter', 1)

        p = g.db.execute_one_dict('''
            SELECT type FROM project WHERE id = %s
        ''', [project_id])

        if not p:
            abort(404)

        project_type = p['type']

        if branch and project_type in ('github', 'gerrit'):
            r = g.db.execute_one_dict('''
                SELECT
                    count(CASE WHEN tr.state = 'ok' THEN 1 END) success,
                    count(CASE WHEN tr.state = 'failure' THEN 1 END) failure,
                    count(CASE WHEN tr.state = 'error' THEN 1 END) error,
                    count(CASE WHEN tr.state = 'skipped' THEN 1 END) skipped
                FROM test_run tr
                WHERE  tr.project_id = %s
                    AND tr.job_id IN (
                        SELECT j.id
                        FROM job j
                        WHERE j.project_id = %s
                            AND j.build_id = (
                                SELECT b.id
                                FROM build b
                                INNER JOIN job j
                                ON b.id = j.build_id
                                    AND b.project_id = %s
                                    AND j.project_id = %s
                                    AND j.name LIKE CONCAT(%s, '%%')
                                INNER JOIN "commit" c
                                    ON c.id = b.commit_id
                                    AND c.project_id = b.project_id
                                    AND c.branch = %s
                                ORDER BY j.created_at DESC
                                LIMIT 1
                            )
                            AND j.name LIKE CONCAT(%s, '%%')
                    )
            ''', [project_id, project_id, project_id, project_id, job_name, branch, job_name])
        elif build_number and build_restart_count:
            r = g.db.execute_one_dict('''
                SELECT
                    count(CASE WHEN tr.state = 'ok' THEN 1 END) success,
                    count(CASE WHEN tr.state = 'failure' THEN 1 END) failure,
                    count(CASE WHEN tr.state = 'error' THEN 1 END) error,
                    count(CASE WHEN tr.state = 'skipped' THEN 1 END) skipped
                FROM test_run tr
                WHERE  tr.project_id = %s
                    AND tr.job_id IN (
                        SELECT j.id
                        FROM job j
                        WHERE j.project_id = %s
                            AND j.build_id = (
                                SELECT b.id
                                FROM build b
                                INNER JOIN job j
                                ON b.id = j.build_id
                                    AND j.state in ('finished', 'unstable')
                                    AND b.project_id = %s
                                    AND j.project_id = %s
                                    AND j.name LIKE CONCAT(%s, '%%')
                                    AND b.build_number = %s
                                    AND b.restart_counter = %s
                                    LIMIT 1
                            )
                            AND j.name LIKE CONCAT(%s, '%%')
                    )
            ''', [project_id, project_id, project_id, project_id,
                  job_name, build_number, build_restart_count, job_name])
        else:
            r = g.db.execute_one_dict('''
                SELECT
                    count(CASE WHEN tr.state = 'ok' THEN 1 END) success,
                    count(CASE WHEN tr.state = 'failure' THEN 1 END) failure,
                    count(CASE WHEN tr.state = 'error' THEN 1 END) error,
                    count(CASE WHEN tr.state = 'skipped' THEN 1 END) skipped
                FROM test_run tr
                WHERE  tr.project_id = %s
                    AND tr.job_id IN (
                        SELECT j.id
                        FROM job j
                        WHERE j.project_id = %s
                            AND j.build_id = (
                                SELECT b.id
                                FROM build b
                                INNER JOIN job j
                                ON b.id = j.build_id
                                    AND j.state in ('finished', 'unstable')
                                    AND b.project_id = %s
                                    AND j.project_id = %s
                                    AND j.name LIKE CONCAT(%s, '%%')
                                ORDER BY j.end_date DESC
                                LIMIT 1
                            )
                            AND j.name LIKE CONCAT(%s, '%%')
                    )
            ''', [project_id, project_id, project_id, project_id, job_name, job_name])

        total = int(r['success']) + int(r['failure']) + int(r['error'])
        status = '%s / %s' % (r['success'], total)

        return get_badge('infrabox', status, 'brightgreen')

@ns.route('/badge.svg')
@api.doc(security=[])
class Badge(Resource):

    @nocache
    def get(self, project_id):
        '''
        Badge
        '''
        job_name = request.args.get('job_name', None)
        subject = request.args.get('subject', None)
        branch = request.args.get('branch', None)
        build_number = request.args.get('build_number', None)
        build_restart_count = request.args.get('build_restart_counter', 1)

        p = g.db.execute_one_dict('''
            SELECT type FROM project WHERE id = %s
        ''', [project_id])

        project_type = p['type']

        if branch and project_type in ('github', 'gerrit'):
            badge = g.db.execute_one_dict('''
                SELECT status, color
                FROM job_badge jb
                JOIN job j
                    ON j.id = jb.job_id
                    AND j.project_id = %s
                    AND j.state in ('finished', 'unstable')
                    AND j.name = %s
                    AND jb.subject = %s
                JOIN build b
                    ON j.build_id = b.id
                    AND b.project_id = %s
                INNER JOIN "commit" c
                    ON c.id = b.commit_id
                    AND c.project_id = b.project_id
                    AND c.branch = %s
                ORDER BY j.end_date desc
                LIMIT 1
            ''', [project_id, job_name, subject, project_id, branch])
        elif build_number and build_restart_count:
            badge = g.db.execute_one_dict('''
                SELECT status, color
                FROM job_badge jb
                JOIN job j
                    ON j.id = jb.job_id
                    AND j.project_id = %s
                    AND j.state in ('finished', 'unstable')
                    AND j.name = %s
                    AND jb.subject = %s
                JOIN build b
                    ON j.build_id = b.id
                    AND b.project_id = %s
                    AND b.build_number = %s
                    AND b.restart_counter = %s
            ''', [project_id, job_name, subject, project_id, build_number, build_number])
        else:
            badge = g.db.execute_one_dict('''
                SELECT status, color
                FROM job_badge jb
                JOIN job j
                    ON j.id = jb.job_id
                    AND j.project_id = %s
                    AND j.state in ('finished', 'unstable')
                    AND j.name = %s
                    AND jb.subject = %s
                JOIN build b
                    ON j.build_id = b.id
                    AND b.project_id = %s
                ORDER BY j.end_date desc
                LIMIT 1
            ''', [project_id, job_name, subject, project_id])

        if not badge:
            abort(404)

        return get_badge(subject, badge['status'], badge['color'])


upload_parser = api.parser()
upload_parser.add_argument('project.zip', location='files',
                           type=FileStorage, required=True)

@ns.route('/archive')
@api.response(403, 'Not Authorized')
class Archive(Resource):
    def get(self, project_id):
        job_name = request.args.get('job_name', None)
        filename = request.args.get('filename', None)
        branch = request.args.get('branch', None)
        if not filename or not job_name:
            abort(404)

        p = g.db.execute_one_dict('''
            SELECT type, name FROM project WHERE id = %s
        ''', [project_id])
        project_type = p['type']
        project_name = p['name']

        result = None

        if branch and project_type in ('github', 'gerrit'):
            result = g.db.execute_one_dict('''
                SELECT j.id, name, c.id commit_id, b.build_number, b.restart_counter, c.branch
                FROM (
                    SELECT id, name, unnest(archive) AS archive, definition->>'name' AS realname, start_date, build_id
                    FROM job
                    WHERE project_id = %s
                ) j
                JOIN build b ON b.id = j.build_id
                JOIN "commit" c ON b.commit_id = c.id
                WHERE archive->>'filename' = %s AND realname = %s AND c.branch = %s
                ORDER BY start_date DESC;
            ''', [project_id, filename, job_name, branch])
        else:
            result = g.db.execute_one_dict('''
                SELECT j.id, name, c.id commit_id, b.build_number, b.restart_counter, c.branch
                FROM (
                    SELECT id, name, unnest(archive) AS archive, definition->>'name' AS realname, start_date, build_id
                    FROM job
                    WHERE project_id = %s
                ) j
                JOIN build b ON b.id = j.build_id
                LEFT JOIN commit c ON b.commit_id = c.id
                WHERE archive->>'filename' = %s AND realname = %s
                ORDER BY start_date DESC;
            ''', [project_id, filename, job_name])

        if not result:
            abort(404)

        job_id = result['id']

        build_number = '{build_number}.{restart_counter}'.format(
            build_number=result['build_number'], restart_counter=result['restart_counter']
        )
        root_url = get_root_url('global')
        build_url = '%s/dashboard/#/project/%s/build/%s/%s' % (root_url,
                                                               project_name,
                                                               result['build_number'],
                                                               result['restart_counter'])
        job_url = '%s/job/%s' % (build_url, result['name'])

        headers = {
            'Infrabox-Build-Number': build_number,
            'Infrabox-Build-Url': build_url,
            'Infrabox-Job-Url': job_url,
        }
        if result['branch']:
            headers['Infrabox-Branch'] = result['branch']
        if result['commit_id']:
            headers['Infrabox-Commit'] = result['commit_id']

        f = storage.download_archive('%s/%s' % (job_id, filename))

        if not f:
            abort(404)

        filename = os.path.basename(filename)

        resp = make_response(send_file(f, attachment_filename=filename,
                                       mimetype=mimetypes.guess_type(filename)[0]))
        resp.headers = headers
        return resp

@ns.route('/upload/<build_id>/')
@api.expect(upload_parser)
class UploadRemote(Resource):

    @api.response(200, 'Success', response_model)
    def post(self, project_id, build_id):
        '''
        Upload and trigger build
        '''
        project = g.db.execute_one_dict('''
            SELECT type
            FROM project
            WHERE id = %s
        ''', [project_id])

        if not project:
            abort(404, 'Project not found')

        if project['type'] != 'upload':
            abort(400, 'Project is not of type "upload"')

        key = '%s.zip' % build_id
        if not storage.exists(key):
            stream = request.files['project.zip'].stream
            storage.upload_project(stream, key)

        return OK('successfully uploaded data')


if enable_upload_forward:
    @ns.route('/upload/', doc=False)
    @api.expect(upload_parser)
    class Upload(Resource):

        @api.response(200, 'Success', response_model)
        def post(self, project_id):
            project = g.db.execute_one_dict('''
                SELECT type
                FROM project
                WHERE id = %s
            ''', [project_id])

            if not project:
                abort(404, 'Project not found')

            if project['type'] != 'upload':
                abort(400, 'Project is not of type "upload"')

            build_id = str(uuid.uuid4())
            key = '%s.zip' % build_id

            stream = request.files['project.zip'].stream
            storage.upload_project(stream, key)

            clusters = g.db.execute_many_dict('''
                SELECT root_url
                FROM cluster
                WHERE active = true
                AND enabled = true
                AND name != %s
            ''', [os.environ['INFRABOX_CLUSTER_NAME']])

            for c in clusters:
                stream.seek(0)
                url = '%s/api/v1/projects/%s/upload/%s/' % (c['root_url'], project_id, build_id)
                files = {'project.zip': stream}
                token = encode_project_token(g.token['id'], project_id, 'myproject')
                headers = {'Authorization': 'bearer ' + token}
                logger.info('Also uploading to %s', url)

                # TODO(ib-steffen): allow custom ca bundles
                r = requests.post(url, files=files, headers=headers, timeout=120, verify=False)

                if r.status_code != 200:
                    abort(500, "Failed to upload data")

            build_number = g.db.execute_one_dict('''
                SELECT count(distinct build_number) + 1 AS build_number
                FROM build AS b
                WHERE b.project_id = %s
            ''', [project_id])['build_number']

            source_upload_id = g.db.execute_one('''
                INSERT INTO source_upload(filename, project_id, filesize) VALUES (%s, %s, 0) RETURNING ID
            ''', [key, project_id])[0]

            g.db.execute('''
                INSERT INTO build (commit_id, build_number, project_id, source_upload_id, id)
                VALUES (null, %s, %s, %s, %s)
            ''', [build_number, project_id, source_upload_id, build_id])

            definition = {
                'build_only': False,
                'resources': {
                    'limits': {
                        'cpu': 0.5,
                        'memory': 1024
                    }
                }
            }

            g.db.execute('''
                INSERT INTO job (id, state, build_id, type, name, project_id,
                                 dockerfile, definition, cluster_name)
                VALUES (gen_random_uuid(), 'queued', %s, 'create_job_matrix',
                        'Create Jobs', %s, '', %s, %s);
            ''', [build_id, project_id, json.dumps(definition), None])

            project_name = g.db.execute_one('''
                SELECT name FROM project WHERE id = %s
            ''', [project_id])[0]

            root_url = get_root_url('global')
            url = '%s/dashboard/#/project/%s/build/%s/1' % (root_url,
                                                            project_name,
                                                            build_number)

            data = {
                'build': {
                    'id': build_id,
                    'number': build_number
                },
                'url': url
            }

            g.db.commit()

            return OK('successfully started build', data=data)
