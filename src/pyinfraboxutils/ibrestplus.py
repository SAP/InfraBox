from flask_restplus import Api, abort as restplus_abort
from flask_restplus.api import SwaggerView

from pyinfraboxutils.ibflask import app

class IBApi(Api):
    def __init__(self):
        authorizations = {
            'TokenAuth': {
                'type': 'basic'
            }
        }

        super(IBApi, self).__init__(app,
                                    authorizations=authorizations,
                                    security=['TokenAuth'],
                                    doc='/api/doc/',
                                    validate=True,
                                    add_specs=False)

    def _register_specs(self, app_or_blueprint):
        endpoint = str('specs')
        self._register_view(
            app_or_blueprint,
            SwaggerView,
            '/api/swagger.json',
            endpoint=endpoint,
            resource_class_args=(self, )
        )

        self.endpoints.add(endpoint)

api = IBApi()

def abort(code, message, data=None):
    restplus_abort(code, message, data=data)
