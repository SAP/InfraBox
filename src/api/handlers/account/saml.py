import uuid
import os
import requests

from flask import g, request, abort, redirect

from flask_restplus import Resource

from pyinfraboxutils import get_logger, get_root_url
from pyinfraboxutils.ibrestplus import api
from pyinfraboxutils.token import encode_user_token

logger = get_logger('saml')

@api.route('/saml/auth')
class SamlAuth(Resource):

    def get(self):
        if os.environ['INFRABOX_SAML_LOGIN_ENABLED'] != 'true':
            abort(404)

        url = ""

        return redirect(url)

@api.route('/saml/callback', doc=False)
class SamlCallback(Resource):

    def get(self):
        # Check if user exists in DB
        # Insert non-existent user to database
        g.db.commit()

        #token = encode_user_token(user_id)
        url = get_root_url('global') + '/dashboard/'
        #logger.error(url)
        res = redirect(url)
        #res.set_cookie('token', token)
        return res
