import os

from flask import g, request, abort

from flask_restplus import Resource, fields

import ldap

from pyinfraboxutils import get_logger
from pyinfraboxutils.ibflask import OK
from pyinfraboxutils.token import encode_user_token
from pyinfraboxutils.ibrestplus import api

from dashboard_api.namespaces import account as ns

login_model = api.model('Login', {
    'email': fields.String(required=True),
    'password': fields.String(required=True),
})

logger = get_logger('ldap')

def authenticate(email, password):
    ldap_server = os.environ['INFRABOX_ACCOUNT_LDAP_URL']
    ldap_user = os.environ['INFRABOX_ACCOUNT_LDAP_DN']
    ldap_password = os.environ['INFRABOX_ACCOUNT_LDAP_PASSWORD']
    ldap_base_dn = os.environ['INFRABOX_ACCOUNT_LDAP_BASE']

    search_filter = "(mail=%s)" % str(email)
    user_dn = None

    print ldap
    connect = ldap.initialize(ldap_server)
    try:
        connect.bind_s(ldap_user, ldap_password)
        result = connect.search_s(ldap_base_dn, ldap.SCOPE_SUBTREE, search_filter, attrlist=['dn'])

        for r in result:
            if r[0]:
                user_dn = r[0]
                break

        if not user_dn:
            abort(400, 'user/password invalid')
    except Exception as e:
        logger.warning("authentication error: %s", e)
        abort(400, 'user/password invalid')
    finally:
        connect.unbind_s()

    try:
        connect = ldap.initialize(ldap_server)
        connect.bind_s(user_dn, password)
        result = connect.search_s(ldap_base_dn,
                                  ldap.SCOPE_SUBTREE,
                                  search_filter,
                                  attrlist=['dn', 'cn', 'displayName'])

        user = result[0]
        if not user or not user[0]:
            abort(400, 'user/password invalid')

            return {
                'cn': user[1]['cn'][0],
                'displayName': user[1]['displayName'][0]
            }

    except Exception as e:
        logger.exception(e)
        abort(400, 'user/password invalid')
    finally:
        connect.unbind_s()

@ns.route('/login')
class Login(Resource):

    @api.expect(login_model)
    def post(self):
        b = request.get_json()

        email = b['email']
        password = b['password']

        ldap_user = authenticate(email, password)

        user = g.db.execute_one_dict('''
            SELECT id FROM "user"
            WHERE email = %s
        ''', [email])

        if not user:
            user = g.db.execute_one_dict('''
                INSERT INTO "user" (email, username, name)
                VALUES (%s, %s, %s) RETURNING id
            ''', [email, ldap_user['cn'], ldap_user['displayName']])

        token = encode_user_token(user['id'])

        g.db.commit()

        res = OK('Logged in')
        res.set_cookie('token', token)
        return res
