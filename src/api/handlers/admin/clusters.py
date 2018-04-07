from flask import g, abort, request
from flask_restplus import Resource, fields

from pyinfraboxutils.ibflask import auth_required

from api.namespaces import admin as ns

@ns.route('/clusters/')
class Clusters(Resource):

    @auth_required(['user'], check_admin=True)
    def get(self):
        clusters = g.db.execute_many_dict('''
            SELECT name, nodes, memory_capacity, cpu_capacity,
                active
            FROM cluster
            ORDER BY name
        ''')

        return clusters
