#pylint: disable=unused-argument
from flask import g, jsonify, abort, send_file
from flask_restplus import Resource

from pyinfraboxutils import get_env, get_logger
from pyinfraboxutils.ibflask import auth_token_required, check_job_belongs_to_project
from pyinfraboxutils.ibrestplus import api
from pyinfraboxutils.storage import storage

ns = api.namespace('api/v1/project/<project_id>/job/<job_id>',
                   description='Job related operations')

logger = get_logger('asd')

@ns.route('/output')
class Output(Resource):

    @auth_token_required(['project'])
    @check_job_belongs_to_project
    def get(self, project_id, job_id):
        key = '%s.tar.gz' % job_id
        f = storage.download_output(key)

        if not f:
            abort(404)

        return send_file(f, attachment_filename=key)

@ns.route('/manifest')
class Project(Resource):

    @auth_token_required(['project'])
    @check_job_belongs_to_project
    def get(self, project_id, job_id):
        m = g.db.execute_one_dict('''
            SELECT j.name, j.start_date, j.end_date, j.cpu, memory, j.state, j.id, b.build_number
            FROM job j
            JOIN build b
                ON b.id = j.build_id
                AND b.project_id = j.project_id
            WHERE j.id = %s
            AND j.project_id = %s
        ''', [job_id, project_id])
        m = dict(m)

        image = get_env('INFRABOX_DOCKER_REGISTRY_URL') + '/' + \
                project_id + '/' + \
                m['name'] + ':build_' + \
                str(m['build_number'])
        image = image.replace("https://", "")
        image = image.replace("http://", "")
        image = image.replace("//", "/")
        m['image'] = image

        m['output'] = {
            'url': get_env('INFRABOX_ROOT_URL') + \
                   '/api/v1/project/' + project_id + \
                   '/job/' + job_id + '/output',
            'format': 'tar.gz'
        }

        deps = g.db.execute_many_dict('''
             SELECT name, state, id FROM job
             WHERE id IN (SELECT (p->>'job-id')::uuid
                          FROM job, jsonb_array_elements(job.dependencies) as p
                          WHERE job.id = %s)
        ''', [job_id])

        for d in deps:
            d['output'] = {
                'url': get_env('INFRABOX_ROOT_URL') + \
                       '/api/v1/project/' + project_id + \
                       '/job/' + d['id'] + '/output',
                'format': 'tar.gz'
            }

            m['dependencies'] = deps

        return jsonify(m)
