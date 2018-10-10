import os

from flask_restplus import Resource, fields

from pyinfraboxutils.ibrestplus import api

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
            'INFRABOX_GERRIT_ENABLED': os.environ['INFRABOX_GERRIT_ENABLED'] == 'true',
            'INFRABOX_ACCOUNT_SIGNUP_ENABLED': os.environ['INFRABOX_ACCOUNT_SIGNUP_ENABLED'] == 'true',
            'INFRABOX_ACCOUNT_LDAP_ENABLED': os.environ['INFRABOX_ACCOUNT_LDAP_ENABLED'] == 'true',
            'INFRABOX_ROOT_URL': os.environ['INFRABOX_ROOT_URL'],
            'INFRABOX_GENERAL_REPORT_ISSUE_URL': os.environ['INFRABOX_GENERAL_REPORT_ISSUE_URL'],
            'INFRABOX_CLUSTER_NAME': os.environ['INFRABOX_CLUSTER_NAME'],
        }

        if github_enabled:
            o['INFRABOX_GITHUB_LOGIN_ENABLED'] = os.environ['INFRABOX_GITHUB_LOGIN_ENABLED'] == 'true'

        return o
