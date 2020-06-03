from flask import g, request, jsonify
from flask_restx import Resource, fields
from pyinfraboxutils.ibflask import OK

from pyinfraboxutils.ibrestplus import api


cluster_setting_model = api.model('ClusterSetting', {
    'name': fields.String(required=True),
    'enabled': fields.Boolean(required=True),
})

@api.route('/api/v1/admin/clusters', doc=False)
class Clusters(Resource):

    def get(self):
        clusters = g.db.execute_many_dict('''
            SELECT name, active, enabled, last_update::text, last_active::text
            FROM "cluster"
            ORDER BY name
        ''')

        return jsonify(clusters)

    @api.expect(cluster_setting_model, validate=True)
    def post(self):
        body = request.get_json()
        g.db.execute('''
            UPDATE cluster
            SET enabled=%s
            WHERE name=%s
        ''', [body['enabled'], body['name']])
        g.db.commit()

        return OK("OK")
