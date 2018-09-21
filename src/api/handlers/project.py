import uuid
import urllib
import os
import json

from datetime import datetime
from functools import wraps, update_wrapper

import requests

from flask import g, request, abort, make_response, Response
from flask_restplus import Resource, fields

from werkzeug.datastructures import FileStorage

from pyinfraboxutils import get_logger

from pyinfraboxutils.ibflask import auth_required, OK
from pyinfraboxutils.ibrestplus import api
from pyinfraboxutils.storage import storage
from pyinfraboxutils.token import encode_project_token

logger = get_logger('api')

ns = api.namespace('api/v1/projects', description='Project related operations')

enable_upload_forword = False

if os.environ['INFRABOX_HA_ENABLED'] == 'true':
    enable_upload_forword = True
elif os.environ['INFRABOX_CLUSTER_NAME'] == 'master':
    enable_upload_forword = True


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

def get_badge(url):
    resp = requests.get(url)

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]

    response = Response(resp.content, resp.status_code, headers)
    return response

project_model = api.model('ProjectModel', {
    'id': fields.String,
    'name': fields.String,
    'type': fields.String,
    'public': fields.Boolean
})

@ns.route('/<project_id>')
class Project(Resource):

    @auth_required(['user', 'project'])
    @api.marshal_with(project_model)
    def get(self, project_id):
        p = g.db.execute_one_dict("""
            SELECT name, id, type, public
            FROM project
            WHERE id = %s
        """, [project_id])
        return p

@ns.route('/<project_id>/state.svg')
@api.doc(security=[])
class State(Resource):

    @nocache
    def get(self, project_id):
        p = g.db.execute_one_dict("""
            SELECT type FROM project WHERE id = %s
        """, [project_id])

        if not p:
            abort(404)

        project_type = p['type']

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

            if state in ('failure', 'error', 'killed'):
                status = state
                color = 'red'

        url = 'https://img.shields.io/badge/infrabox-%s-%s.svg' % (status, color)
        return get_badge(url)

@ns.route('/<project_id>/tests.svg')
@api.doc(security=[])
class Tests(Resource):

    @nocache
    def get(self, project_id):
        branch = request.args.get('branch', None)
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
                                INNER JOIN "commit" c
                                    ON c.id = b.commit_id
                                    AND c.project_id = b.project_id
                                    AND c.branch = %s
                                ORDER BY j.created_at DESC
                                LIMIT 1
                            )
                    )
            ''', [project_id, project_id, project_id, project_id, branch])
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
                                    AND b.project_id = %s
                                    AND j.project_id = %s
                                ORDER BY j.created_at DESC
                                LIMIT 1
                            )
                    )
            ''', [project_id, project_id, project_id, project_id])

        total = int(r['success']) + int(r['failure']) + int(r['error'])
        status = '%s / %s' % (r['success'], total)

        return get_badge('https://img.shields.io/badge/infrabox-%s-%s.svg' % (status,
                                                                              'brightgreen'))

@ns.route('/<project_id>/badge.svg')
@api.doc(security=[])
class Badge(Resource):

    @nocache
    def get(self, project_id):
        job_name = request.args.get('job_name', None)
        subject = request.args.get('subject', None)
        branch = request.args.get('branch', None)
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
                    AND j.state = 'finished'
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
        else:
            badge = g.db.execute_one_dict('''
                SELECT status, color
                FROM job_badge jb
                JOIN job j
                    ON j.id = jb.job_id
                    AND j.project_id = %s
                    AND j.state = 'finished'
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

        status = urllib.quote(badge['status'])
        subject = urllib.quote(subject)

        return get_badge('https://img.shields.io/badge/%s-%s-%s.svg' % (subject,
                                                                        status,
                                                                        badge['color']))


upload_parser = api.parser()
upload_parser.add_argument('project.zip', location='files',
                           type=FileStorage, required=True)


@ns.route('/<project_id>/upload/<build_id>/')
@ns.expect(upload_parser)
class UploadRemote(Resource):

    @auth_required(['project'])
    def post(self, project_id, build_id):
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

        stream = request.files['project.zip'].stream
        storage.upload_project(stream, key)

        return OK('successfully uploaded data')


if enable_upload_forword:
    @ns.route('/<project_id>/upload/')
    @ns.expect(upload_parser)
    class Upload(Resource):

        @auth_required(['project'])
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
                token = encode_project_token(g.token['id'], project_id)
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

            url = '%s/dashboard/#/project/%s/build/%s/1' % (os.environ['INFRABOX_ROOT_URL'],
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
