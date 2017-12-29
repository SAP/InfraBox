import uuid
import urllib

from flask import g, jsonify, request, abort, redirect
from flask_restplus import Resource

from werkzeug.datastructures import FileStorage

from pyinfraboxutils.ibflask import auth_token_required, OK
from pyinfraboxutils.ibrestplus import api
from pyinfraboxutils.storage import storage

ns = api.namespace('api/v1/project', description='Project related operations')

@ns.route('/<project_id>')
class Project(Resource):

    @auth_token_required(['user', 'project'])
    def get(self, project_id):
        p = g.db.execute_one_dict('''
            SELECT name, id, type, public, build_on_push
            FROM project
            WHERE id = %s
        ''', [project_id])
        return jsonify(p)

@ns.route('/<project_id>/state.svg')
class State(Resource):

    def get(self, project_id):
        p = g.db.execute_one_dict('''
            SELECT type FROM project WHERE id = %s
        ''', [project_id])

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
            print state
            if state in ('running', 'queued', 'scheduled'):
                status = 'running'
                color = 'grey'
                break

            if state in ('failure', 'error', 'killed'):
                status = state
                color = 'red'

        return redirect('https://img.shields.io/badge/infrabox-%s-%s.svg' % (status, color), code=307)

@ns.route('/<project_id>/tests.svg')
class Tests(Resource):

    def get(self, project_id):
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

        return redirect('https://img.shields.io/badge/infrabox-%s-%s.svg' % (status,
                                                                             'brightgreen'), code=307)



@ns.route('/<project_id>/badge.svg')
class Badge(Resource):

    def get(self, project_id):
        job_name = request.args.get('job_name', None)
        subject = request.args.get('subject', None)

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

        return redirect('https://img.shields.io/badge/%s-%s-%s.svg' % (subject,
                                                                       status,
                                                                       badge['color']), code=307)


upload_parser = api.parser()
upload_parser.add_argument('project.zip', location='files',
                           type=FileStorage, required=True)

@ns.route('/<project_id>/upload/')
@ns.expect(upload_parser)
class Upload(Resource):

    @auth_token_required(['project'])
    def post(self, project_id):
        build_id = str(uuid.uuid4())
        key = '%s.zip' % build_id

        storage.upload_project(request.files['project.zip'].stream, key)

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

        g.db.execute('''
            INSERT INTO job (id, state, build_id, type, name, project_id,
                             dockerfile, build_only, cpu, memory)
            VALUES (gen_random_uuid(), 'queued', %s, 'create_job_matrix',
                    'Create Jobs', %s, '', false, 1, 1024);
        ''', [build_id, project_id])

        data = {
            'build': {
                'id': build_id,
                'number': build_number
            }
        }

        g.db.commit()

        return OK('successfully stasrted build', data=data)
