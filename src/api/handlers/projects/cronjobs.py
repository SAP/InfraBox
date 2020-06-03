import re

from flask import request, g, abort
from flask_restx import Resource, fields

from pyinfrabox.utils import validate_uuid
from pyinfraboxutils.ibflask import OK
from pyinfraboxutils.ibrestplus import api, response_model

from croniter import croniter

ns = api.namespace('CronJobs',
                   path='/api/v1/projects/<project_id>/cronjobs',
                   description='Cronjob related operations')

cronjob_model = api.model('CronJob', {
    'name': fields.String(required=True),
    'id': fields.String(required=True),
    'minute': fields.String(required=True),
    'hour': fields.String(required=True),
    'day_month': fields.String(required=True),
    'month': fields.String(required=True),
    'day_week': fields.String(required=True),
    'sha': fields.String(required=True),
    'infrabox_file': fields.String(required=True, max_length=255),
})

add_cronjob_model = api.model('AddCronJob', {
    'name': fields.String(required=True, max_length=255),
    'minute': fields.String(required=True, max_length=255),
    'hour': fields.String(required=True, max_length=255),
    'day_month': fields.String(required=True, max_length=255),
    'month': fields.String(required=True, max_length=255),
    'day_week': fields.String(required=True, max_length=255),
    'sha': fields.String(required=True, max_length=255),
    'infrabox_file': fields.String(required=True, max_length=255),
})

@ns.route('/')
@api.doc(responses={403: 'Not Authorized'})
class CronJobs(Resource):

    name_pattern = re.compile('^[a-zA-Z0-9_]+$')

    @api.marshal_list_with(cronjob_model)
    def get(self, project_id):
        '''
        Returns project's cronjobs
        '''
        p = g.db.execute_many_dict('''
            SELECT * FROM cronjob
            WHERE project_id = %s
        ''', [project_id])
        return p

    @api.expect(add_cronjob_model)
    @api.response(200, 'Success', response_model)
    def post(self, project_id):
        '''
        Create new cronjob
        '''
        b = request.get_json()

        if not CronJobs.name_pattern.match(b['name']):
            abort(400, 'CronJob name must be not empty alphanumeric string.')

        if not croniter.is_valid('%s %s %s %s %s' % (b['minute'], b['hour'], b['day_month'], b['month'], b['day_week'])):
            abort(400, 'Invalid input expression')

        result = g.db.execute_one_dict("""
            SELECT COUNT(*) as cnt FROM cronjob WHERE project_id = %s
        """, [project_id])

        if result['cnt'] > 50:
            abort(400, 'Too many cronjobs.')

        r = g.db.execute_one("""
                    SELECT count(*) FROM cronjob
                    WHERE project_id = %s AND name = %s
                """, [project_id, b['name']])

        if r[0] > 0:
            abort(400, 'CronJob with this name already exist')

        g.db.execute('''
            INSERT INTO cronjob (project_id, name, minute, hour, day_month, month, day_week, sha, infrabox_file) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', [project_id, b['name'], b['minute'], b['hour'], b['day_month'], b['month'], b['day_week'], b['sha'], b['infrabox_file']])

        g.db.commit()

        return OK('Successfully added CronJob.')

@ns.route('/<cronjob_id>')
@api.doc(responses={403: 'Not Authorized'})
class CronJob(Resource):
    @api.response(200, 'Success', response_model)
    def delete(self, project_id, cronjob_id):
        '''
        Delete a cronjob
        '''
        if not validate_uuid(cronjob_id):
            abort(400, "Invalid cronjob uuid.")

        num_cronjobs = g.db.execute_one("""
            SELECT COUNT(*) FROM cronjob
            WHERE project_id = %s and id = %s
        """, [project_id, cronjob_id])[0]

        if num_cronjobs == 0:
            return abort(400, 'Cronjob does not exist.')

        g.db.execute("""
            DELETE FROM cronjob WHERE project_id = %s and id = %s
        """, [project_id, cronjob_id])
        g.db.commit()

        return OK('Successfully deleted cronjob.')
