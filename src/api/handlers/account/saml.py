from urlparse import urlparse

from flask import g, request, abort, redirect, make_response

from flask_restx import Resource

from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.utils import OneLogin_Saml2_Utils

from pyinfraboxutils import get_logger, get_root_url, get_env
from pyinfraboxutils.ibrestplus import api
from pyinfraboxutils.token import encode_user_token

logger = get_logger("saml")

get_env("INFRABOX_ACCOUNT_SAML_SETTINGS_PATH")
get_env("INFRABOX_ACCOUNT_SAML_EMAIL_FORMAT")
get_env("INFRABOX_ACCOUNT_SAML_NAME_FORMAT")
get_env("INFRABOX_ACCOUNT_SAML_USERNAME_FORMAT")

def init_saml_auth():
    parsed_url = urlparse(request.url)
    request_data = {
        "https": "on" if request.scheme == "https" else "off",
        "http_host": request.host,
        "server_port": parsed_url.port,
        "script_name": request.path,
        "get_data": request.args.copy(),
        "post_data": request.form.copy(),
        "query_string": request.query_string
        }

    auth = OneLogin_Saml2_Auth(request_data, custom_base_path=get_env("INFRABOX_ACCOUNT_SAML_SETTINGS_PATH"))
    return auth

def get_attribute_dict(saml_auth):
    attributes = {}
    nested_attribute_dict = saml_auth.get_attributes()
    for attribute_name, nested_attribute in nested_attribute_dict.items():
        if len(nested_attribute) > 0:
            attributes[attribute_name] = nested_attribute[0]
    attributes["NameID"] = saml_auth.get_nameid()
    return attributes

def format_user_field(format_string, attributes):
    try:
        return format_string.format(**attributes)
    except KeyError as e_key:
        logger.error("The IdP did not provide a required attribute: %s", e_key)
        abort(500)

@api.route("/saml/auth")
class SamlAuth(Resource):

    def get(self):
        auth = init_saml_auth()
        return redirect(auth.login())

@api.route("/saml/callback")
class SamlCallback(Resource):

    def post(self):
        auth = init_saml_auth()
        auth.process_response()
        errors = auth.get_errors()

        logger.info("Request: %s %s", request, request.headers)

        if len(errors) != 0:
            logger.error("Authentication failed: %s", "; ".join(errors))
            abort(500, "Authentication failed")

        if not auth.is_authenticated():
            logger.error("User returned unauthorized from IdP")
            abort(401, "Unauthorized")

        attributes = get_attribute_dict(auth)
        logger.debug("User data: %s", attributes)

        email = format_user_field(get_env("INFRABOX_ACCOUNT_SAML_EMAIL_FORMAT"), attributes).lower()

        # Check if user already exists in database
        user = g.db.execute_one_dict("""
                SELECT id FROM "user"
                WHERE email = %s
            """, [email])

        if not user:
            name = format_user_field(get_env("INFRABOX_ACCOUNT_SAML_NAME_FORMAT"), attributes)
            username = format_user_field(get_env("INFRABOX_ACCOUNT_SAML_USERNAME_FORMAT"), attributes)

            user = g.db.execute_one_dict("""
                INSERT INTO "user" (name, username, email)
                VALUES (%s, %s, %s) RETURNING id
            """, [name, username, email])

        token = encode_user_token(user["id"])

        g.db.commit()

        redirect_url = get_root_url("global") + "/dashboard/"
        logger.debug("Redirecting authenticated user to %s", redirect_url)
        response = redirect(redirect_url)
        response.set_cookie("token", token)
        return response

@api.route("/saml/metadata")
class SamlMetadata(Resource):
    def get(self):
        auth = init_saml_auth()
        settings = auth.get_settings()
        metadata = settings.get_sp_metadata()
        metadata_errors = settings.validate_metadata(metadata)

        if len(metadata_errors) != 0:
            logger.error("SP Metadata contains errors: %s", "; ".join(metadata_errors))
            abort(500)

        response = make_response(metadata, 200)
        response.headers["Content-Type"] = "application/xml"
        return response

# Endpoint for SAML Single Logout / SLO (Callback)
@api.route("/saml/logout")
class SamlLogout(Resource):
    def get(self):
        auth = init_saml_auth()
        try:
            redirect_url = auth.process_slo()
        except Exception as e:
            logger.error("Single Logout failed: %s", e)
            return redirect(get_root_url("global"))
        errors = auth.get_errors()
        if len(errors) != 0:
            logger.error("Single Logout failed: %s", "; ".join(errors))
            return redirect(get_root_url("global"))

        if redirect_url is None:
            redirect_url = redirect_url = get_root_url("global")

        response = redirect(redirect_url)
        response.set_cookie("token", "", expires=0)
        return response

# Endpoint for initiating a SAML Single Logout / SLO
@api.route("/saml/initiate-logout")
class SamlInitiateLogout(Resource):
    def get(self):
        auth = init_saml_auth()
        try:
            return redirect(auth.logout())
        except Exception as e:
            logger.error("Could not initiate Single Logout: %s", e)
            return redirect(get_root_url("global"))