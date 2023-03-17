from flask import request, g, abort
from flask_restx import Resource, fields

from pyinfraboxutils.ibflask import OK
from pyinfraboxutils.ibrestplus import api, response_model

ns = api.namespace('Vault',
                   path='/api/v1/projects/<project_id>/vault',
                   description='Vault service related operations')

project_vault_model = api.model('VaultService', {
    'name': fields.String(required=True),
    'url': fields.String(required=True),
    'namespace': fields.String(required=False),
    'version': fields.String(required=True),
    'token': fields.String(required=True),
    'ca': fields.String(required=False),
    'role_id': fields.String(required=False),
    'secret_id': fields.String(required=False),
    'id': fields.String(required=False)
})


@ns.route('/')
@api.doc(responses={403: 'Not Authorized'})
class Vault(Resource):

    @api.marshal_with(project_vault_model)
    def get(self, project_id):
        '''
        Returns project's vault service
        '''
        v = g.db.execute_many_dict('''
            SELECT id, name, url, namespace, version, token, ca, role_id, secret_id
            FROM vault
            WHERE project_id = %s
        ''', [project_id])
        return v

    @api.expect(project_vault_model)
    def post(self, project_id):
        b = request.get_json()
        if not b['name'] or not b['url'] or not ['version']:
            abort(400, "Invalid Vault format")
        if not b['token']:
            if not b['role_id'] or not b['secret_id']:
                abort(400, "Invalid Vault format")
        g.db.execute('''
                    INSERT INTO vault (project_id, name, url, namespace, version, token, ca, role_id, secret_id) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', [project_id, b['name'], b['url'], b['namespace'], b['version'], b['token'], b['ca'], b['role_id'], b['secret_id']])
        g.db.commit()
        return OK('Successfully added vault.')


@ns.route('/<vault_id>')
@api.doc(responses={403: 'Not Authorized'})
class Vault(Resource):
    @api.response(200, 'Success', response_model)
    def delete(self, project_id, vault_id):
        g.db.execute('''
                    DELETE FROM vault WHERE project_id = %s and id = %s
                ''', [project_id, vault_id])
        g.db.commit()
        return OK('Successfully deleted vault.')
