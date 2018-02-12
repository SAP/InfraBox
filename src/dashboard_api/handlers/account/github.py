import uuid
import os
import requests

from flask import g, request, abort, redirect

from flask_restplus import Resource

from pyinfraboxutils.token import encode_user_token

from dashboard_api.namespaces import github as ns

GITHUB_CLIENT_ID = os.environ['INFRABOX_GITHUB_CLIENT_ID']
GITHUB_CLIENT_SECRET = os.environ['INFRABOX_GITHUB_CLIENT_SECRET']
GITHUB_CALLBACK_URL = os.environ['INFRABOX_ROOT_URL'] + "/github/auth/callback"
GITHUB_AUTHORIZATION_URL = os.environ['INFRABOX_GITHUB_LOGIN_URL'] + "/oauth/authorize"
GITHUB_TOKEN_URL = os.environ['INFRABOX_GITHUB_LOGIN_URL'] + "/oauth/access_token"
GITHUB_USER_PROFILE_URL = os.environ['INFRABOX_GITHUB_API_URL'] + "/user"

states = {}

@ns.route('/auth')
class Auth(Resource):

    def get(self):
        state = uuid.uuid4()
        url = GITHUB_AUTHORIZATION_URL
        url += '?client_id=%s&scope=%s&state=%s' % (GITHUB_CLIENT_ID,
                                                    '%20'.join(['user:email', 'repo', 'read:org']),
                                                    state)

        states[str(state)] = True
        return redirect(url)

@ns.route('/auth/callback')
class Login(Resource):

    def get(self):
        state = request.args.get('state')
        code = request.args.get('code')

        if not states.get(state, None):
            abort(401)

        del states[state]

        r = requests.post(GITHUB_TOKEN_URL, data={
            'client_id': GITHUB_CLIENT_ID,
            'client_secret': GITHUB_CLIENT_SECRET,
            'code': code,
            'state': state
        }, headers={'Accept': 'application/json'})
        result = r.json()

        access_token = result['access_token']
        r = requests.get(GITHUB_USER_PROFILE_URL, headers={
            'Accept': 'application/json',
            'Authorization': 'token %s' % access_token
        })
        gu = r.json()

        github_id = gu['id']
        user = g.db.execute_one_dict('''
            SELECT id FROM "user"
            WHERE github_id = %s
        ''', [github_id])

        if not user:
            user = g.db.execute_one_dict('''
                INSERT INTO "user" (github_id, username, avatar_url, name)
                VALUES (%s, %s, %s, %s) RETURNING id
            ''', [github_id, gu['login'], gu['avatar_url'], gu['name']])

        user_id = user['id']

        g.db.execute('''
            UPDATE "user" SET github_api_token = %s
            WHERE id = %s
        ''', [access_token, user_id])

        g.db.commit()

        token = encode_user_token(user_id)

        res = redirect('/dashboard')
        res.set_cookie('token', token)
        return res
