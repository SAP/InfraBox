from flask import g, request
from flask_restplus import Resource

from pyinfraboxutils.ibrestplus import api


cluster_setting_model = api.model('ClusterSetting', {
    'name': fields.String(required=True),
    'enabled': fields.Boolean(required=True),
})

@api.route('/api/v1/admin/clusters', doc=False)
class Clusters(Resource):

    def get(self):
        clusters = g.db.execute_many_dict('''
            SELECT name, active, enabled, last_update, last_active
            FROM "cluster"
            ORDER BY name
        ''')

        return clusters

    @api.expect(cluster_setting_model, validate=True)
    def post(self):
        body = request.get_json()
        g.db.execute('''
            UPDATE clusters
            SET enabled=%s
            WHERE name=%s
        ''', [body['enabled'], body['name']])
