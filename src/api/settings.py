import os

from flask_restx import Resource, fields

from pyinfraboxutils.ibrestplus import api
from pyinfraboxutils import get_root_url

ns = api.namespace('Settings',
                   path='/api/v1/settings',
                   description='Settings related operations')


settings_model = api.model('User', {
    'INFRABOX_GITHUB_ENABLED': fields.Boolean,
    'INFRABOX_GERRIT_ENABLED': fields.Boolean,
    'INFRABOX_ACCOUNT_SIGNUP_ENABLED': fields.Boolean,
    'INFRABOX_ACCOUNT_LDAP_ENABLED': fields.Boolean,
    'INFRABOX_ROOT_URL': fields.String,
    'INFRABOX_GENERAL_REPORT_ISSUE_URL': fields.String,
    'INFRABOX_CLUSTER_NAME': fields.String,
    'INFRABOX_GITHUB_LOGIN_ENABLED': fields.Boolean,
    'INFRABOX_SSO_LOGIN_ENABLED': fields.Boolean,
    'INFRABOX_LEGAL_PRIVACY_URL': fields.String,
    'INFRABOX_LEGAL_TERMS_OF_USE_URL': fields.String
})

@ns.route('')
class Settings(Resource):

    @api.marshal_with(settings_model)
    def get(self):
        '''
        Returns the cluster settings
        '''
        github_enabled = os.environ['INFRABOX_GITHUB_ENABLED'] == 'true'
        o = {
            'INFRABOX_GITHUB_ENABLED': github_enabled,
            'INFRABOX_SSO_LOGIN_ENABLED': os.environ['INFRABOX_ACCOUNT_SAML_ENABLED'] == 'true',
            'INFRABOX_GERRIT_ENABLED': os.environ['INFRABOX_GERRIT_ENABLED'] == 'true',
            'INFRABOX_ACCOUNT_SIGNUP_ENABLED': os.environ['INFRABOX_ACCOUNT_SIGNUP_ENABLED'] == 'true',
            'INFRABOX_ACCOUNT_LDAP_ENABLED': os.environ['INFRABOX_ACCOUNT_LDAP_ENABLED'] == 'true',
            'INFRABOX_ROOT_URL': get_root_url('global'),
            'INFRABOX_GENERAL_REPORT_ISSUE_URL': os.environ['INFRABOX_GENERAL_REPORT_ISSUE_URL'],
            'INFRABOX_CLUSTER_NAME': os.environ['INFRABOX_CLUSTER_NAME'],
            'INFRABOX_LEGAL_PRIVACY_URL':  os.environ['INFRABOX_LEGAL_PRIVACY_URL'],
            'INFRABOX_LEGAL_TERMS_OF_USE_URL':  os.environ['INFRABOX_LEGAL_TERMS_OF_USE_URL'],
        }

        if github_enabled:
            o['INFRABOX_GITHUB_LOGIN_ENABLED'] = os.environ['INFRABOX_GITHUB_LOGIN_ENABLED'] == 'true'

        return o
