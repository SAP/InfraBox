from flask_restplus import Api, abort as restplus_abort, Resource, fields
from pyinfraboxutils.ibflask import app

authorizations = {
    'TokenAuth': {
        'type': 'basic'
    }
}

api = Api(app, authorizations=authorizations,
          doc='/api/doc/',
          validate=True,
          add_specs=False)

@api.route('/api/swagger.json')
class Swagger(Resource):
    def get(self):
        '''
        swagger.json
        '''
        return api.__schema__

response_model = api.model('Response', {
    'message': fields.String,
    'status': fields.Integer,
})

def abort(code, message, data=None):
    restplus_abort(code, message, data=data)
