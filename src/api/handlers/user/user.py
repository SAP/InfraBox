from flask import g, abort
from flask_restx import Resource, fields

from pyinfraboxutils.ibflask import OK
from pyinfraboxutils.ibrestplus import api

ns = api.namespace('User',
                   path='/api/v1/user',
                   description='User related operations')

user_model = api.model('User', {
    'github_id': fields.Integer,
    'username': fields.String,
    'avatar_url': fields.String,
    'name': fields.String,
    'email': fields.String,
    'id': fields.String,
    'role': fields.String(enum=['user', 'devops', 'admin'])
})

@ns.route('')
@api.doc(responses={403: 'Not Authorized'})
@api.doc(responses={404: 'User not found'})
class User(Resource):

    @api.marshal_with(user_model)
    def get(self):
        '''
        Returns information about the current user
        '''

        user = g.db.execute_one_dict('''
            SELECT github_id, username, avatar_url, name, email, id, role
            FROM "user"
            WHERE id = %s
        ''', [g.token['user']['id']])

        if not user:
            abort(404)

        return user
