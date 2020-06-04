import re

from flask import request, g, abort
from flask_restx import Resource, fields

from pyinfrabox.utils import validate_uuid
from pyinfraboxutils.ibflask import OK
from pyinfraboxutils.ibrestplus import api, response_model

ns = api.namespace('SSHKeys',
                   path='/api/v1/projects/<project_id>/sshkeys',
                   description='SSH Key related operations')

sshkey_model = api.model('CronJob', {
    'name': fields.String(required=True),
    'id': fields.String(required=True),
    'secret': fields.String(required=True),
})

add_sshkey_model = api.model('AddCronJob', {
    'name': fields.String(required=True, max_length=255),
    'secret': fields.String(required=True, max_length=255),
})

@ns.route('/')
@api.doc(responses={403: 'Not Authorized'})
class SSHKeys(Resource):

    name_pattern = re.compile('^[a-zA-Z0-9_]+$')

    @api.marshal_list_with(sshkey_model)
    def get(self, project_id):
        '''
        Returns project's sshkeys
        '''
        p = g.db.execute_many_dict('''
            SELECT k.id, k.name, s.name as secret
            FROM sshkey k
            JOIN secret s
            ON  s.id = k.secret_id
            WHERE s.project_id = %s
            AND k.project_id = %s
        ''', [project_id, project_id])
        return p

    @api.expect(add_sshkey_model)
    @api.response(200, 'Success', response_model)
    def post(self, project_id):
        '''
        Add new sshkey
        '''
        b = request.get_json()

        if not SSHKeys.name_pattern.match(b['name']):
            abort(400, 'CronJob name must be not empty alphanumeric string.')

        result = g.db.execute_one_dict("""
            SELECT id
            FROM secret
            WHERE project_id = %s
            AND name = %s
        """, [project_id, b['secret']])

        if not result:
            abort(400, 'Secret does not exist')

        secret_id = result['id']

        result = g.db.execute_one_dict("""
            SELECT COUNT(*) as cnt
            FROM sshkey
            WHERE project_id = %s
        """, [project_id])

        if result['cnt'] > 0:
            abort(400, 'Too many sshkeys')

        r = g.db.execute_one("""
            SELECT count(*)
            FROM sshkey
            WHERE project_id = %s
            AND name = %s
        """, [project_id, b['name']])

        if r[0] > 0:
            abort(400, 'SSH Key with this name already exist')

        g.db.execute('''
            INSERT INTO sshkey (project_id, name, secret_id) VALUES(%s, %s, %s)
        ''', [project_id, b['name'], secret_id])

        g.db.commit()

        return OK('Successfully added SSH Key')

@ns.route('/<sshkey_id>')
@api.doc(responses={403: 'Not Authorized'})
class CronJob(Resource):
    @api.response(200, 'Success', response_model)
    def delete(self, project_id, sshkey_id):
        '''
        Delete a sshkey
        '''
        if not validate_uuid(sshkey_id):
            abort(400, "Invalid sshkey uuid.")

        num_sshkeys = g.db.execute_one("""
            SELECT COUNT(*) FROM sshkey
            WHERE project_id = %s and id = %s
        """, [project_id, sshkey_id])[0]

        if num_sshkeys == 0:
            return abort(400, 'SSH Key does not exist.')

        g.db.execute("""
            DELETE FROM sshkey WHERE project_id = %s and id = %s
        """, [project_id, sshkey_id])
        g.db.commit()

        return OK('Successfully deleted SSH Key.')
