import re

from flask import request, g, abort
from flask_restx import Resource, fields


from pyinfrabox.utils import validate_uuid
from pyinfraboxutils.ibflask import OK
from pyinfraboxutils.ibrestplus import api, response_model
from pyinfraboxutils.secrets import encrypt_secret

ns = api.namespace('Secrets',
                   path='/api/v1/projects/<project_id>/secrets',
                   description='Secret related operations')

secret_model = api.model('Secret', {
    'name': fields.String(required=True),
    'id': fields.String(required=True),
})

add_secret_model = api.model('AddSecret', {
    'name': fields.String(required=True, max_length=255),
    'value': fields.String(required=True, max_length=1024 * 128),
})

@ns.route('/')
@api.doc(responses={403: 'Not Authorized'})
class Secrets(Resource):

    name_pattern = re.compile('^[a-zA-Z0-9_]+$')

    @api.marshal_list_with(secret_model)
    def get(self, project_id):
        '''
        Returns project's secrets
        '''
        p = g.db.execute_many_dict('''
            SELECT name, id FROM secret
            WHERE project_id = %s
        ''', [project_id])
        return p

    @api.expect(add_secret_model)
    @api.response(200, 'Success', response_model)
    def post(self, project_id):
        '''
        Create new secret
        '''
        b = request.get_json()

        if not Secrets.name_pattern.match(b['name']):
            abort(400, 'Secret name must be not empty alphanumeric string.')

        result = g.db.execute_one_dict("""
            SELECT COUNT(*) as cnt FROM secret WHERE project_id = %s
        """, [project_id])

        if result['cnt'] > 200:
            abort(400, 'Too many secrets.')

        r = g.db.execute_one("""
                    SELECT count(*) FROM secret
                    WHERE project_id = %s AND name = %s
                """, [project_id, b['name']])

        if r[0] > 0:
            abort(400, 'Secret with this name already exist.')

        value = encrypt_secret(b['value'])

        g.db.execute('''
            INSERT INTO secret (project_id, name, value) VALUES(%s, %s, %s)
        ''', [project_id, b['name'], value])

        g.db.commit()

        return OK('Successfully added secret.')


@ns.route('/<secret_id>')
@api.doc(responses={403: 'Not Authorized'})
class Secret(Resource):
    @api.response(200, 'Success', response_model)
    def delete(self, project_id, secret_id):
        '''
        Delete a secret
        '''
        if not validate_uuid(secret_id):
            abort(400, "Invalid secret uuid.")

        num_secrets = g.db.execute_one("""
            SELECT COUNT(*) FROM secret
            WHERE project_id = %s and id = %s
        """, [project_id, secret_id])[0]

        if num_secrets == 0:
            return abort(400, 'Such secret does not exist.')

        num_keys = g.db.execute_one("""
            SELECT COUNT(*) FROM sshkey
            WHERE project_id = %s and secret_id = %s
        """, [project_id, secret_id])[0]

        if num_keys != 0:
            return abort(400, 'Secret is still used SSH Key.')

        g.db.execute("""
            DELETE FROM secret WHERE project_id = %s and id = %s
        """, [project_id, secret_id])
        g.db.commit()

        return OK('Successfully deleted secret.')
