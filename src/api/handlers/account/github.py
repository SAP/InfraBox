import uuid
import os
import requests

from flask import g, request, abort, redirect

from flask_restx import Resource

from pyinfraboxutils import get_logger, get_root_url
from pyinfraboxutils.ibrestplus import api
from pyinfraboxutils.token import encode_user_token

logger = get_logger('github')

GITHUB_CLIENT_ID = os.environ['INFRABOX_GITHUB_CLIENT_ID']
GITHUB_CLIENT_SECRET = os.environ['INFRABOX_GITHUB_CLIENT_SECRET']
GITHUB_AUTHORIZATION_URL = os.environ['INFRABOX_GITHUB_LOGIN_URL'] + "/oauth/authorize"
GITHUB_TOKEN_URL = os.environ['INFRABOX_GITHUB_LOGIN_URL'] + "/oauth/access_token"
GITHUB_USER_PROFILE_URL = os.environ['INFRABOX_GITHUB_API_URL'] + "/user"
GITHUB_CALLBACK_URL = get_root_url('global') + "/github/auth/callback"

# TODO(ib-steffen): move into DB
states = {}

def get_next_page(r):
    link = r.headers.get('Link', None)

    if not link:
        return None

    n1 = link.find('rel=\"next\"')

    if n1 < 0:
        return None

    n2 = link.rfind('<', 0, n1)

    if n2 < 0:
        return None

    n2 += 1
    n3 = link.find('>;', n2)
    return link[n2:n3]

def get_github_api(url, token):
    headers = {
        "Authorization": "token " + token,
        "User-Agent": "InfraBox"
    }
    url = os.environ['INFRABOX_GITHUB_API_URL'] + url

    # TODO(ib-steffen): allow custom ca bundles
    r = requests.get(url, headers=headers, verify=False)
    result = []
    result.extend(r.json())

    p = get_next_page(r)
    while p:
        r = requests.get(p, headers=headers, verify=False)
        p = get_next_page(r)
        result.extend(r.json())

    return result

@api.route('/github/auth/connect', doc=False)
class Connect(Resource):

    def get(self):
        if os.environ['INFRABOX_GITHUB_LOGIN_ENABLED'] == 'true':
            abort(404)

        user_id = g.token['user']['id']
        uid = str(uuid.uuid4())

        g.db.execute('''
            UPDATE "user" SET github_id = null, github_api_token = %s
            WHERE id = %s
        ''', [uid, user_id])

        g.db.commit()

        state = str(uuid.uuid4())
        url = GITHUB_AUTHORIZATION_URL
        url += '?client_id=%s&scope=%s&state=%s&redirect_uri=%s' % (GITHUB_CLIENT_ID,
                                                                    '%20'.join(['user:email', 'repo', 'read:org']),
                                                                    state,
                                                                    '%s%%3Ft=%s' % (GITHUB_CALLBACK_URL, uid))

        states[str(state)] = True
        return redirect(url)


@api.route('/api/v1/github/repos', doc=False)
class Repos(Resource):

    def get(self):
        user_id = g.token['user']['id']

        user = g.db.execute_one_dict('''
            SELECT github_api_token
            FROM "user"
            WHERE id = %s
        ''', [user_id])

        if not user:
            abort(404)

        token = user['github_api_token']
        github_repos = get_github_api('/user/repos?visibility=all', token)

        repos = g.db.execute_many_dict('''
            select github_id from collaborator co
            INNER JOIN repository r
            ON co.project_id = r.project_id
            WHERE user_id = %s
            AND github_id is not null
        ''', [user_id])

        for gr in github_repos:
            gr['connected'] = False

            for r in repos:
                if r['github_id'] == gr['id']:
                    gr['connected'] = True
                    break

        return github_repos

@api.route('/github/auth', doc=False)
class Auth(Resource):

    def get(self):
        if os.environ['INFRABOX_GITHUB_LOGIN_ENABLED'] != 'true':
            abort(404)

        state = uuid.uuid4()
        url = GITHUB_AUTHORIZATION_URL
        url += '?client_id=%s&scope=%s&state=%s' % (GITHUB_CLIENT_ID,
                                                    '%20'.join(['user:email', 'repo', 'read:org']),
                                                    state)

        states[str(state)] = True
        return redirect(url)

def check_org(access_token):
    allowed_orgs = os.environ.get('INFRABOX_GITHUB_LOGIN_ALLOWED_ORGANIZATIONS', None)

    if not allowed_orgs:
        return

    allowed_orgs = allowed_orgs.split(',')

    orgs = get_github_api('/user/orgs', access_token)

    for o in orgs:
        for ao in allowed_orgs:
            if o['login'] == ao:
                return

    abort(401, "Not allowed to signup")

@api.route('/github/auth/callback', doc=False)
class Login(Resource):

    def get(self):
        state = request.args.get('state')
        code = request.args.get('code')
        t = request.args.get('t', None)

        if not states.get(state, None):
            abort(401)

        del states[state]

        # TODO(ib-steffen): allow custom ca bundles
        r = requests.post(GITHUB_TOKEN_URL, data={
            'client_id': GITHUB_CLIENT_ID,
            'client_secret': GITHUB_CLIENT_SECRET,
            'code': code,
            'state': state
        }, headers={'Accept': 'application/json'}, verify=False)

        if r.status_code != 200:
            logger.error(r.text)
            abort(500)

        result = r.json()

        access_token = result['access_token']
        check_org(access_token)

        # TODO(ib-steffen): allow custom ca bundles
        r = requests.get(GITHUB_USER_PROFILE_URL, headers={
            'Accept': 'application/json',
            'Authorization': 'token %s' % access_token
        }, verify=False)
        gu = r.json()

        github_id = gu['id']

        if os.environ['INFRABOX_GITHUB_LOGIN_ENABLED'] == 'true':
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
        else:
            if not t:
                abort(404)

            user = g.db.execute_one_dict('''
                SELECT id
                FROM "user"
                WHERE github_api_token = %s
            ''', [t])

            if not user:
                abort(404)

            user_id = user['id']

        g.db.execute('''
            UPDATE "user" SET github_api_token = %s, github_id = %s
            WHERE id = %s
        ''', [access_token, github_id, user_id])

        g.db.commit()

        token = encode_user_token(user_id)
        url = get_root_url('global') + '/dashboard/'
        logger.debug("Redirecting GitHub user to %s", url)
        res = redirect(url)
        res.set_cookie('token', token)
        return res
