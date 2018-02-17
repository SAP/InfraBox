from flask_restplus import Api, abort as restplus_abort

from pyinfraboxutils.ibflask import app

authorizations = {
    'TokenAuth': {
        'type': 'basic'
    }
}

api = Api(app,
          authorizations=authorizations,
          security=['TokenAuth'],
          doc='/doc/',
          validate=True)

def abort(code, message, data=None):
    restplus_abort(code, message, data=data)
