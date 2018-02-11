import os

from flask import jsonify
from flask_restplus import Resource

from pyinfraboxutils.ibrestplus import api

project = api.namespace('api/dashboard/projects/',
                        description='Project related operations')

settings = api.namespace('api/dashboard/settings/',
                         description='Settings')

user = api.namespace('api/dashboard/user/',
                     description='User')

account = api.namespace('api/dashboard/account/',
                        description='Account')


@settings.route('/')
class Settings(Resource):

    def get(self):
        o = {
            'INFRABOX_GITHUB_ENABLED': os.environ['INFRABOX_GITHUB_ENABLED'],
            'INFRABOX_GERRIT_ENABLED': os.environ['INFRABOX_GERRIT_ENABLED'],
            'INFRABOX_ACCOUNT_SIGNUP_ENABLED': os.environ['INFRABOX_ACCOUNT_SIGNUP_ENABLED'],
            'INFRABOX_ACCOUNT_LDAP_ENABLED': os.environ['INFRABOX_ACCOUNT_LDAP_ENABLED'],
            'INFRABOX_ROOT_URL': os.environ['INFRABOX_ROOT_URL']
        }

        return jsonify(o)

