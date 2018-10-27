from datetime import datetime

import eventlet
from eventlet import wsgi
eventlet.monkey_patch()

from flask import jsonify, g, request
from flask_restplus import Resource

from pyinfraboxutils import get_env, get_logger
from pyinfraboxutils.ibflask import app
from pyinfraboxutils.ibrestplus import api
from pyinfraboxutils.db import connect_db

logger = get_logger('api')

app.config['OPA_ENABLED'] = False

@app.route('/ping')
def ping():
    return jsonify({'status': 200})

@app.route('/v2/') # prevent 301 redirects
@app.route('/v2')
def v2():
    return jsonify({'status': 200})

@api.route("/api/job/consoleupdate", doc=False)
class ConsoleUpdate(Resource):
    def post(self):
        records = request.json

        data = {}
        for r in records:
            if 'kubernetes' not in r:
                continue

            job_id = r['kubernetes']['labels']['job-name'][:-4]

            a = float(r['date'])
            date = datetime.fromtimestamp(float(a)).strftime("%H:%M:%S")
            log = "%s|%s" % (date, r['log'])

            if not data.get(job_id):
                data[job_id] = ""

            data[job_id] += log

        for job_id, log in data.items():
            r = g.db.execute_one("""
                SELECT state
                FROM job
                WHERE id = %s
            """, [job_id])

            if not r:
                continue

            if r[0] not in ('scheduled', 'running'):
                continue

            g.db.execute("INSERT INTO console (job_id, output) VALUES (%s, %s)", [job_id, log])
            g.db.execute("""
                UPDATE job SET state = 'running', start_date = current_timestamp
                WHERE id = %s and state = 'scheduled'""", [job_id])
            g.db.commit()

        return {}


def main(): # pragma: no cover
    get_env('INFRABOX_VERSION')
    get_env('INFRABOX_DATABASE_HOST')
    get_env('INFRABOX_DATABASE_USER')
    get_env('INFRABOX_DATABASE_PASSWORD')
    get_env('INFRABOX_DATABASE_PORT')
    get_env('INFRABOX_DATABASE_DB')

    connect_db()
    wsgi.server(eventlet.listen(('0.0.0.0', 8080)), app)

if __name__ == "__main__": # pragma: no cover
    main()
