from flask import g, jsonify
from flask_restplus import Resource

from pyinfraboxutils.ibflask import auth_token_required
from pyinfraboxutils.ibrestplus import api

ns = api.namespace('api/v1/project/<project_id>/build/<build_id>', description='Build related operations')

@ns.route('/job')
class Job(Resource):

    @auth_token_required(['user', 'project'])
    def get(self, project_id, build_id):
        p = g.db.execute_many_dict('''
            SELECT j.name, j.start_date, j.end_date, j.cpu, j.memory, j.state, j.id
            FROM job j
            INNER JOIN build b
                ON j.build_id = b.id
                AND j.project_id = %s
                AND b.project_id = %s
                AND b.id = %s
        ''', [project_id, project_id, build_id])
        return jsonify(p)
