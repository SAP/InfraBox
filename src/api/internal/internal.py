from datetime import datetime

from flask import g, request
from flask_restx import Resource

from pyinfraboxutils.ibrestplus import api, response_model
from api.handlers.trigger import trigger_model, trigger_build

ns = api.namespace('Internal',
                   path='/internal/api',
                   description='Project related operations')

@ns.route('/projects/<project_id>/trigger', doc=False)
@api.response(404, 'Project not found')
class Trigger(Resource):

    @api.expect(trigger_model)
    @api.response(200, 'Success', response_model)
    def post(self, project_id):
        '''
        Trigger a new build
        '''
        return trigger_build(project_id)


@ns.route("/job/consoleupdate", doc=False)
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
            log = log.replace('\x00', '\n')

            if not data.get(job_id):
                data[job_id] = ""

            data[job_id] += log

        for job_id, log in data.items():
            if not log:
                continue

            r = g.db.execute_one("""
                SELECT state
                FROM job
                WHERE id = %s
            """, [job_id])

            if not r:
                continue

            if r[0] not in ('scheduled', 'running'):
                continue

            g.db.execute("""
                INSERT INTO console (job_id, output) VALUES (%s, %s);
            """, [job_id, log])
            g.db.commit() # Commit here, updating job state later on might fail

            g.db.execute("""
                UPDATE job SET state = 'running', start_date = current_timestamp
                WHERE id = %s
                AND state = 'scheduled'
            """, [job_id])
            g.db.commit()

        return {}
