from urlparse import urlparse

from flask import g, request, abort, redirect, make_response

from flask_restplus import Resource

from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.utils import OneLogin_Saml2_Utils

from pyinfraboxutils import get_logger, get_root_url, get_env
from pyinfraboxutils.ibrestplus import api
from pyinfraboxutils.token import encode_user_token

logger = get_logger('saml')

def init_saml_auth():
    parsed_url = urlparse(request.url)
    request_data = {
        'https': 'on' if request.scheme == 'https' else 'off',
        'http_host': request.host,
        'server_port': parsed_url.port,
        'script_name': request.path,
        'get_data': request.args.copy(),
        'post_data': request.form.copy(),
        'query_string': request.query_string
        }
    
    auth = OneLogin_Saml2_Auth(request_data, custom_base_path="src/api/handlers/account")
    return auth

@api.route('/saml/auth')
class SamlAuth(Resource):

    def get(self):
        auth = init_saml_auth()
        return redirect(auth.login())

@api.route('/saml/callback')
class SamlCallback(Resource):

    def post(self):
        auth = init_saml_auth()
        auth.process_response()
        errors = auth.get_errors()

        logger.info("Request: %s %s", request, request.headers)

        if len(errors) != 0:
            logger.error("Authentication failed: %s", errors)
            abort(500, "Authentication failed")
        
        if not auth.is_authenticated():
            logger.error("User returned unauthorized from IdP")
            abort(401, "Unauthorized")

        userdata = auth.get_attributes()
        logger.debug("User data: %s", userdata)

        if not 'email' in userdata or len(userdata['email']) == 0:
            logger.error("IdP provided no user email address")
            abort(401, "Unauthorized")

        email = userdata['email']
        if isinstance(email, list):
            email = userdata['email'][0] # Take first email address if there are multiple

        # Check if user already exists in database
        user = g.db.execute_one_dict('''
                SELECT id FROM "user"
                WHERE email = %s
            ''', [email])

        if not user:
            nameid = auth.get_nameid()

            name = nameid
            if 'name' in userdata:
                name = userdata['name']

            user = g.db.execute_one_dict('''
                INSERT INTO "user" (name, username, email)
                VALUES (%s, %s, %s) RETURNING id
            ''', [name, nameid, email])

        token = encode_user_token(user['id'])

        g.db.commit()
        
        redirect_url = get_root_url('global') + '/dashboard/'
        logger.debug("Redirecting authenticated user to %s", redirect_url)
        response = redirect(redirect_url)
        response.set_cookie('token', token)
        return response
        
@api.route('/saml/metadata')
class SamlMetadata(Resource):
    def get(self):
        auth = init_saml_auth()
        settings = auth.get_settings()
        metadata = settings.get_sp_metadata()
        metadata_errors = settings.validate_metadata(metadata)
        
        if len(metadata_errors) != 0:
            logger.error("SP Metadata contains errors: %s", ";".join(metadata_errors))
            abort(500)

        response = make_response(metadata, 200)
        response.headers["Content-Type"] = 'application/xml'
        return response
