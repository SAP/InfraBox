from flask import request, g, abort
from flask_restx import Resource, fields

from pyinfraboxutils.ibflask import OK
from pyinfraboxutils.ibrestplus import api, response_model

ns = api.namespace('Vault',
                   path='/api/v1/projects/<project_id>/vault',
                   description='Vault service related operations')

project_vault_model = api.model('VaultService', {
    'url': fields.String(required=True),
    'token': fields.String(required=True),
    'id': fields.String(required=False)
})

@ns.route('/<vault_id>')
@api.doc(responses={403: 'Not Authorized'})
class Tokens(Resource):

    @api.marshal_with(project_vault_model)
    def get(self, project_id, vault_id):
        '''one
        Returns project's vault service
        '''
        v = g.db.execute_many_dict('''
            SELECT id, url, token
            FROM vault
            WHERE project_id = %s
        ''', [project_id])
        return v

    @api.expect(project_vault_model)
    def post(self, project_id):
        b = request.get_json()
        g.db.execute('''
                    INSERT INTO vault (project_id, url, token) VALUES(%s, %s, %s)
                ''', [project_id, b['url'], b['token']])
        g.db.commit()
        return OK('Successfully added vault.')

    def delete(self, project_id, vault_id):
        g.db.execute('''
                    DELETE FROM vault WHERE project_id = %s and id = %s
                ''', [project_id, vault_id])
        g.db.commit()
        return OK('Successfully deleted vault.')
