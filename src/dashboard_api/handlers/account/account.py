from email.utils import parseaddr

from flask import g, request, abort

from flask_restplus import Resource, fields

import bcrypt

from pyinfraboxutils import get_logger
from pyinfraboxutils.ibflask import OK
from pyinfraboxutils.ibrestplus import api
from pyinfraboxutils.token import encode_user_token


from dashboard_api.namespaces import account as ns

login_model = api.model('Login', {
    'email': fields.String(required=True),
    'password': fields.String(required=True),
})

logger = get_logger('login')

@ns.route('/login')
class Login(Resource):

    @api.expect(login_model)
    def post(self):
        b = request.get_json()

        email = b['email']
        password = b['password']

        user = g.db.execute_one_dict('''
            SELECT id, password
            FROM "user"
            WHERE email = %s
        ''', [email])

        if not user:
            abort(400, 'Invalid email/password combination')

        if not bcrypt.checkpw(password.encode('utf8'), user['password'].encode('utf8')):
            abort(400, 'Invalid email/password combination')

        token = encode_user_token(user['id'])

        res = OK('Logged in')
        res.set_cookie('token', token)
        return res

register_model = api.model('Register', {
    'username': fields.String(required=True),
    'email': fields.String(required=True),
    'password1': fields.String(required=True),
    'password2': fields.String(required=True),
})

@ns.route('/register')
class Register(Resource):

    @api.expect(register_model)
    def post(self):
        b = request.get_json()

        email = b['email']
        password1 = b['password1']
        password2 = b['password2']
        username = b['username']

        if password1 != password2:
            abort(400, 'Passwords don\'t match')

        e = parseaddr(email)

        if not e:
            abort(400, 'Invalid email')

        if not e[1]:
            abort(400, 'Invalid email')

        if not username.isalnum():
            abort(400, 'Username is not alphanumeric')

        user = g.db.execute_one_dict('''
            SELECT id, password
            FROM "user"
            WHERE email = %s
        ''', [email])

        if user:
            abort(400, 'An account with this email already exists')

        hashed_password = bcrypt.hashpw(password1.encode('utf8'), bcrypt.gensalt())
        user = g.db.execute_one_dict('''
            INSERT into "user" (email, password)
            VALUES (%s, %s) RETURNING ID
        ''', [email, hashed_password])

        token = encode_user_token(user['id'])

        g.db.commit()

        res = OK('Logged in')
        res.set_cookie('token', token)
        return res
