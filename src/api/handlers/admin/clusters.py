from flask import g
from flask_restplus import Resource

from pyinfraboxutils.ibflask import auth_required

from api.namespaces import admin as ns

@ns.route('/clusters/')
class Clusters(Resource):

    @auth_required(['user'], check_project_access=False)
    def get(self):
        clusters = g.db.execute_many_dict('''
            SELECT name, nodes, memory_capacity, cpu_capacity,
                active, labels
            FROM cluster
            ORDER BY name
        ''')

        resources = g.db.execute_many_dict('''
	    SELECT cluster_name,
                SUM(CASE WHEN state = 'running' THEN 1 ELSE 0 END) running,
                SUM(CASE WHEN state = 'running' THEN (definition#>>'{resources,limits,cpu}')::decimal ELSE 0 END) running_cpu,
                SUM(CASE WHEN state = 'running' THEN (definition#>>'{resources,limits,memory}')::integer ELSE 0 END) running_memory,
                SUM(CASE WHEN state = 'scheduled' THEN 1 ELSE 0 END) scheduled,
                SUM(CASE WHEN state = 'scheduled' THEN (definition#>>'{resources,limits,cpu}')::decimal ELSE 0 END) scheduled_cpu,
                SUM(CASE WHEN state = 'scheduled' THEN (definition#>>'{resources,limits,memory}')::integer ELSE 0 END) scheduled_memory,
                SUM(CASE WHEN state = 'queued' THEN 1 ELSE 0 END) queued,
                SUM(CASE WHEN state = 'queued' THEN (definition#>>'{resources,limits,cpu}')::decimal ELSE 0 END) queued_cpu,
                SUM(CASE WHEN state = 'queued' THEN (definition#>>'{resources,limits,memory}')::integer ELSE 0 END) queued_memory
	    FROM job
	    GROUP BY cluster_name
        ''')

        for r in resources:
            cluster = None
            for c in clusters:
                if c['name'] == r['cluster_name']:
                    cluster = c

            if not cluster:
                continue

            cluster['jobs'] = {
                'running': r['running'],
                'scheduled': r['scheduled'],
                'queued': r['queued'],
            }

            cluster['cpu'] = {
                'running': r['running_cpu'],
                'scheduled': r['scheduled_cpu'],
                'queued': r['queued_cpu'],
            }

            cluster['memory'] = {
                'running': r['running_memory'],
                'scheduled': r['scheduled_memory'],
                'queued': r['queued_memory'],
            }

        return clusters
