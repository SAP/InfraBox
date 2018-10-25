import uuid
import os
import requests

from urlparse import urlparse

from flask import g, request, abort, redirect

from flask_restplus import Resource

from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.utils import OneLogin_Saml2_Utils

from pyinfraboxutils import get_logger, get_root_url, get_env
from pyinfraboxutils.ibrestplus import api
from pyinfraboxutils.token import encode_user_token

logger = get_logger('saml')

def init_saml_auth(req):
    auth = OneLogin_Saml2_Auth(req, custom_base_path="src/api/handlers/account")
    return auth

def prepare_flask_request(request):
    # If server is behind proxys or balancers use the HTTP_X_FORWARDED fields
    url_data = urlparse(request.url)
    return {
        'https': 'on' if request.scheme == 'https' else 'off',
        'http_host': request.host,
        'server_port': url_data.port,
        'script_name': request.path,
        'get_data': request.args.copy(),
        'post_data': request.form.copy(),
        # Uncomment if using ADFS as IdP, https://github.com/onelogin/python-saml/pull/144
        # 'lowercase_urlencoding': True,
        'query_string': request.query_string
    }

@api.route('/saml/auth')
class SamlAuth(Resource):

    def get(self):
        req = prepare_flask_request(request)
        auth = init_saml_auth(req)

        return redirect(auth.login())

@api.route('/saml/callback', doc=False)
class SamlCallback(Resource):

    def post(self):
        req = prepare_flask_request(request)
        auth = init_saml_auth(req)
        auth.process_response()
        errors = auth.get_errors()
        not_auth_warn = not auth.is_authenticated()
        
        if len(errors) == 0:
            userdata = auth.get_attributes()
            nameid = auth.get_nameid()
            session_index = auth.get_session_index()
            logger.debug("User: %s, nameID: %s, session_index: %s", userdata, nameid, session_index)
            logger.debug("Request: %s", request)
            return redirect(get_env('INFRABOX_ROOT_URL'))
        else:
            raise Exception(errors)
        
                
        # Check if user exists in DB
        # Insert non-existent user to database
        #g.db.commit()

        #token = encode_user_token(user_id)
        #url = get_root_url('global') + '/dashboard/'
        #logger.error(url)
        #res = redirect(url)
        #res.set_cookie('token', token)
        #return res
