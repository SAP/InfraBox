from flask import g, jsonify

import eventlet
from eventlet import wsgi
eventlet.monkey_patch()

from pyinfraboxutils import get_env, get_logger
from pyinfraboxutils.ibflask import app

logger = get_logger('state')
app.config['OPA_ENABLED'] = False

@app.route('/')
def ping():
    return jsonify({})

@app.route('/<cluster_name>')
def s(cluster_name):
    status = g.db.execute_one_dict("""
                SELECT active, enabled
                FROM cluster
                WHERE name = %s
            """, [cluster_name])


    if not status:
        return jsonify({}), 404

    if not status['active'] or not status['enabled']:
        return jsonify(status), 503

    return jsonify({'status': "active"})

def main(): # pragma: no cover
    get_env('INFRABOX_DATABASE_HOST')
    get_env('INFRABOX_DATABASE_USER')
    get_env('INFRABOX_DATABASE_PASSWORD')
    get_env('INFRABOX_DATABASE_PORT')
    get_env('INFRABOX_DATABASE_DB')

    wsgi.server(eventlet.listen(('0.0.0.0', 8080)), app)

if __name__ == "__main__": # pragma: no cover
    main()
