#pylint: disable=unused-argument
from flask import g, jsonify, abort, send_file
from flask_restx import Resource, fields

from pyinfraboxutils.ibflask import check_job_belongs_to_project
from pyinfraboxutils.ibrestplus import api
from pyinfraboxutils.storage import storage

ns = api.namespace('Jobs',
                   path='/api/v1/projects/<project_id>/jobs/<job_id>',
                   description='Settings related operations')

limits_model = api.model('LimitsModel', {
    'cpu': fields.Integer(min=1, attribute='cpu'),
    'memory': fields.Integer(min=128, attribute='memory')
})

dependency_model = api.model('DependencyModel', {
    'on': fields.List(fields.String),
    'job': fields.String,
    'job-id': fields.String
})

resource_model = api.model('ResourceModel', {
    'limits': fields.Nested(limits_model)
})

job_model = api.model('JobModel', {
    'id': fields.String,
    'name': fields.String,
    'type': fields.String,
    'state': fields.String,
    'start_date': fields.DateTime,
    'end_date': fields.DateTime,
    'resources': fields.Nested(resource_model),
    'message': fields.String,
    'docker_file': fields.String,
    'depends_on': fields.List(fields.Nested(dependency_model)),
})

@ns.route('')
@api.doc(responses={403: 'Not Authorized'})
class Job(Resource):

    @api.marshal_with(job_model)
    def get(self, project_id, job_id):
        '''
        Returns a single job
        '''
        job = g.db.execute_one_dict('''
            SELECT id, state, start_date, build_id, end_date, name,
                definition#>'{resources,limits,cpu}' as cpu,
                definition#>'{resources,limits,memory}' as memory,
                build_arg, env_var, dockerfile as docker_file,
                dependencies as depends_on
            FROM job
            WHERE project_id = %s
            AND id = %s
        ''', [project_id, job_id])

        return job


@ns.route('/output', doc=False)
@api.doc(responses={403: 'Not Authorized'})
class Output(Resource):

    @check_job_belongs_to_project
    def get(self, project_id, job_id):
        '''
        Returns the the content of /infrabox/output of the job
        '''
        g.release_db()

        key = '%s.tar.snappy' % job_id
        f = storage.download_output(key)

        if not f:
            abort(404)

        return send_file(f, attachment_filename=key)

@ns.route('/manifest', doc=False)
@api.doc(responses={403: 'Not Authorized'})
class Project(Resource):

    @check_job_belongs_to_project
    def get(self, project_id, job_id):
        result = g.db.execute_one_dict('''
            SELECT j.name, j.start_date, j.end_date,
                   definition#>'{resources,limits,cpu}' as cpu,
                   definition#>'{resources,limits,memory}' as memory,
                   j.state, j.id, b.build_number, j.env_var, j.env_var_ref, c.root_url
            FROM job j
            JOIN build b
                ON b.id = j.build_id
                AND b.project_id = j.project_id
            JOIN cluster c
                ON j.cluster_name = c.name
            WHERE j.id = %s
            AND j.project_id = %s
        ''', [job_id, project_id])

        if not result:
            abort(404)

        root_url = result['root_url']

        m = {
            'name': result['name'],
            'start_date': result['start_date'],
            'end_date': result['end_date'],
            'cpu': result['cpu'],
            'memory': result['memory'],
            'state': result['state'],
            'id': result['id'],
            'build_number': result['build_number'],
            'environment': result['env_var'],
            'image': None,
            'output': None,
            'dependencies': []
        }

        # Image
        image = root_url + '/' + \
                project_id + '/' + \
                result['name'] + ':build_' + \
                str(result['build_number'])
        image = image.replace("https://", "")
        image = image.replace("http://", "")
        image = image.replace("//", "/")
        m['image'] = image

        # Output
        m['output'] = {
            'url': root_url + \
                   '/api/v1/projects/' + project_id + \
                   '/jobs/' + job_id + '/output',
            'format': 'tar.snappy'
        }

        # Dependencies
        deps = g.db.execute_many_dict('''
             SELECT j.name, j.state, j.id, c.root_url
             FROM job j
             JOIN cluster c
             ON j.cluster_name = c.name
             WHERE id IN (SELECT (p->>'job-id')::uuid
                          FROM job, jsonb_array_elements(job.dependencies) as p
                          WHERE job.id = %s)
        ''', [job_id])

        for d in deps:
            d['output'] = {
                'url': d['root_url'] + \
                       '/api/v1/projects/' + project_id + \
                       '/jobs/' + d['id'] + '/output',
                'format': 'tar.snappy'
            }

            m['dependencies'].append(d)

        return jsonify(m)
