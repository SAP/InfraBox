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
    'id': fields.String(required=False)
})

@ns.route('/')
@api.doc(responses={403: 'Not Authorized'})
class Tokens(Resource):

    @api.marshal_with(project_vault_model)
    def get(self, project_id):
        '''one
        Returns project's vault service
        '''
        v = g.db.execute_many_dict('''
            SELECT id, name, url, namespace, version, token, ca
            FROM vault
            WHERE project_id = %s
        ''', [project_id])
        return v

    @api.expect(project_vault_model)
    def post(self, project_id):
        b = request.get_json()
        g.db.execute('''
                    INSERT INTO vault (project_id, name, url, namespace, version, token, ca) VALUES(%s, %s, %s, %s, %s, %s, %s)
                ''', [project_id, b['name'], b['url'], b['version'], b['token'], b['ca']])
        g.db.commit()
        return OK('Successfully added vault.')


@ns.route('/<vault_id>')
@api.doc(responses={403: 'Not Authorized'})
class Secret(Resource):
    @api.response(200, 'Success', response_model)
    def delete(self, project_id, vault_id):
        g.db.execute('''
                    DELETE FROM vault WHERE project_id = %s and id = %s
                ''', [project_id, vault_id])
        g.db.commit()
        return OK('Successfully deleted vault.')
