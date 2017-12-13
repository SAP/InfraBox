from flask_restplus import Api, abort as restplus_abort

from pyinfraboxutils.ibflask import app

api = Api(app)

def abort(code, message, data=None):
    restplus_abort(code, message, data=data)
