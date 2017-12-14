import uuid

from flask import g, request
from flask_restplus import Resource
from werkzeug.datastructures import FileStorage

from pyinfraboxutils.ibflask import auth_token_required, OK
from pyinfraboxutils.ibrestplus import api
from pyinfraboxutils.storage import storage

ns = api.namespace('api/v1/project/<project_id>/upload', description='Upload related operations')

upload_parser = api.parser()
upload_parser.add_argument('project.zip', location='files',
                           type=FileStorage, required=True)

@ns.route('/')
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
