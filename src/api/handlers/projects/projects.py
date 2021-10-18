import os
import requests

from flask import g, abort, request
from flask_restx import Resource, fields

from pyinfrabox.utils import validate_uuid
from pyinfraboxutils import get_logger, get_root_url
from pyinfraboxutils.ibrestplus import api, response_model
from pyinfraboxutils.ibflask import OK
from pyinfraboxutils.ibopa import opa_push_project_data, opa_push_collaborator_data

from Crypto.PublicKey import RSA

ns = api.namespace('Projects',
                   path='/api/v1/projects',
                   description='Project related operations')


logger = get_logger('project')

project_model = api.model('Project', {
    'id': fields.String(required=True),
    'name': fields.String(required=True),
    'type': fields.String(required=True),
    'public': fields.Boolean(required=True),
    'userrole': fields.String(required=False)
})

add_project_schema = {
    'type': "object",
    'properties': {
        'name': {'type': "string", 'pattern': r"^[0-9a-zA-Z_\-/]+$", "minLength": 3},
        'private': {'type': "boolean"},
        'type': {'type': "string", 'enum': ["upload", "gerrit", "github"]},
        'github_repo_name': {'type': "string"}
    },
    'required': ["name", "private", "type"]
}

add_project_model = api.schema_model('AddProject', add_project_schema)

@ns.route('/')
@api.response(403, 'Not Authorized')
class Projects(Resource):

    @api.marshal_list_with(project_model)
    def get(self):
        '''
        Returns user's projects
        '''
        projects = g.db.execute_many_dict("""
            SELECT p.id, p.name, p.type, p.public, co.role AS userrole
            FROM project p
            INNER JOIN collaborator co
            ON co.project_id = p.id
            AND %s = co.user_id
            ORDER BY p.name
        """, [g.token['user']['id']])

        return projects

    @api.expect(add_project_model)
    @api.response(200, 'Success', response_model)
    def post(self):
        '''
        Create new project
        '''
        user_id = g.token['user']['id']

        b = request.get_json()
        name = b['name']
        typ = b['type']
        private = b['private']

        projects = g.db.execute_one_dict('''
            SELECT COUNT(*) as cnt
            FROM project p
            INNER JOIN collaborator co
            ON p.id = co.project_id
            AND co.user_id = %s
        ''', [user_id])

        if projects['cnt'] > 200:
            abort(400, 'too many projects')

        project = g.db.execute_one_dict('''
            SELECT *
            FROM project
            WHERE name = %s
        ''', [name])

        if project:
            abort(400, 'A project with this name already exists')


        if typ == 'github':
            github_repo_name = b.get('github_repo_name', None)

            if not github_repo_name:
                abort(400, 'github_repo_name not set')

            split = github_repo_name.split('/')
            owner = split[0]
            repo_name = split[1]

            user = g.db.execute_one_dict('''
                SELECT github_api_token
                FROM "user"
                WHERE id = %s
            ''', [user_id])

            if not user:
                abort(404)

            api_token = user['github_api_token']

            headers = {
                "Authorization": "token " + api_token,
                "User-Agent": "InfraBox"
            }
            url = '%s/repos/%s/%s' % (os.environ['INFRABOX_GITHUB_API_URL'],
                                      owner, repo_name)

            # TODO(ib-steffen): allow custom ca bundles
            r = requests.get(url, headers=headers, verify=False)

            if r.status_code != 200:
                abort(400, 'Failed to get github repo')

            repo = r.json()

            if not repo['permissions']['admin']:
                abort(400, 'You are not allowed to connect this repo')

            r = g.db.execute_one_dict('''
                SELECT *
                FROM repository
                WHERE github_id = %s
            ''', [repo['id']])

            if r:
                abort('Repo already connected')

        project = g.db.execute_one_dict('''
            INSERT INTO project (name, type, public)
            VALUES (%s, %s, %s) RETURNING id
        ''', [name, typ, not private])
        project_id = project['id']

        g.db.execute('''
            INSERT INTO collaborator (user_id, project_id, role)
            VALUES (%s, %s, 'Owner')
        ''', [user_id, project_id])


        if typ == 'github':
            split = github_repo_name.split('/')
            owner = split[0]
            repo_name = split[1]

            clone_url = repo['clone_url']
            if repo['private']:
                clone_url = repo['ssh_url']

            g.db.execute('''
                INSERT INTO repository (name, html_url, clone_url, github_id,
                                        private, project_id, github_owner)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', [repo['name'], repo['html_url'], clone_url,
                  repo['id'], repo['private'], project_id, repo['owner']['login']])

            insecure_ssl = "0"
            if os.environ['INFRABOX_GENERAL_DONT_CHECK_CERTIFICATES'] == 'true':
                insecure_ssl = "1"

            webhook_config = {
                'name': "web",
                'active': True,
                'events': [
                    "create", "delete", "public", "pull_request", "push"
                ],
                'config': {
                    'url': get_root_url('global') + '/github/hook',
                    'content_type': "json",
                    'secret': os.environ['INFRABOX_GITHUB_WEBHOOK_SECRET'],
                    'insecure_ssl': insecure_ssl
                }
            }

            headers = {
                "Authorization": "token " + api_token,
                "User-Agent": "InfraBox"
            }
            url = '%s/repos/%s/%s/hooks' % (os.environ['INFRABOX_GITHUB_API_URL'],
                                            owner, repo_name)

            # TODO(ib-steffen): allow custom ca bundles
            r = requests.post(url, headers=headers, json=webhook_config, verify=False)

            if r.status_code != 201:
                abort(400, 'Failed to create github webhook')

            hook = r.json()

            g.db.execute('''
                UPDATE repository SET github_hook_id = %s
                WHERE github_id = %s
            ''', [hook['id'], repo['id']])

            # deploy key
            key = RSA.generate(2048)
            private_key = key.exportKey('PEM')
            public_key = key.publickey().exportKey('OpenSSH')
            deploy_key_config = {
                'title': "InfraBox",
                'key': public_key,
                'read_only': True
            }

            url = '%s/repos/%s/%s/keys' % (os.environ['INFRABOX_GITHUB_API_URL'],
                                           owner, repo_name)

            # TODO(ib-steffen): allow custom ca bundles
            r = requests.post(url, headers=headers, json=deploy_key_config, verify=False)

            if r.status_code != 201:
                abort(400, 'Failed to create deploy key')

            g.db.execute('''
                UPDATE repository SET private_key = %s
                WHERE github_id = %s
            ''', [private_key, repo['id']])

        elif typ == 'gerrit':
            g.db.execute('''
                INSERT INTO repository (name, private, project_id, html_url, clone_url, github_id)
                VALUES (%s, false, %s, '', '', 0)
            ''', [name, project_id])

        g.db.commit()

        # Push updated collaborator and project data to Open Policy Agent
        opa_push_project_data(g.db)
        opa_push_collaborator_data(g.db)

        return OK('Project added')

@ns.route('/name/<path:project_name>')
@api.response(403, 'Not Authorized')
class ProjectName(Resource):

    @api.marshal_with(project_model)
    def get(self, project_name):
        if g.token and g.token["type"] == "user":
            project = g.db.execute_one_dict('''
                SELECT p.id, p.name, p.type, p.public, co.role AS userrole
                FROM project p
                LEFT JOIN collaborator co ON p.id = co.project_id AND co.user_id = %s
                WHERE p.name = %s
            ''', [g.token["user"]["id"], project_name])
        else:
            project = g.db.execute_one_dict('''
                SELECT id, name, type, public
                FROM project
                WHERE name = %s
            ''', [project_name])

        if not project:
            abort(404)

        return project

change_visibility_schema = {
    'type': "object",
    'properties': {
        'private': {'type': "boolean"},
    },
    'required': ["private"]
}

change_visibility_model = api.schema_model('ChangeVisibility', change_visibility_schema)

@ns.route('/<project_id>/visibility')
@api.response(403, 'Not Authorized')
class Project(Resource):

    @api.expect(change_visibility_model)
    @api.response(200, 'Success', response_model)
    def post(self, project_id):
        '''
        Change projects visibility
        '''
        b = request.get_json()
        private = b['private']

        g.db.execute('''
            UPDATE project
            SET public = %s
            WHERE id = %s
        ''', [not private, project_id])

        g.db.commit()
        return OK('updated visibility')

@ns.route('/<project_id>')
@api.response(403, 'Not Authorized')
class Project(Resource):

    @api.marshal_with(project_model)
    def get(self, project_id):
        '''
        Returns a project
        '''

        if g.token and g.token["type"] == "user":
            project = g.db.execute_one_dict('''
                SELECT p.id, p.name, p.type, p.public, co.role AS userrole
                FROM project p
                LEFT JOIN collaborator co ON p.id = co.project_id AND co.user_id = %s
                WHERE p.id = %s
            ''', [g.token["user"]["id"], project_id])
        else:
            project = g.db.execute_one_dict('''
                SELECT p.id, p.name, p.type, p.public
                FROM project p
                WHERE id = %s
            ''', [project_id])

        return project

    @api.response(200, 'Success', response_model)
    def delete(self, project_id):
        '''
        Delete a project
        '''
        if not validate_uuid(project_id):
            abort(400, "Invalid project uuid.")

        project = g.db.execute_one_dict("""
            DELETE FROM project WHERE id = %s RETURNING type
        """, [project_id])

        if not project:
            abort(400, 'Project with such an id does not exist.')

        if project['type'] == 'github':
            repo = g.db.execute_one_dict('''
                SELECT name, github_owner, github_hook_id
                FROM repository
                WHERE project_id = %s
            ''', [project_id])

            gh_owner = repo['github_owner']
            gh_hook_id = repo['github_hook_id']
            gh_repo_name = repo['name']

            user = g.db.execute_one_dict('''
                SELECT github_api_token
                FROM "user"
                WHERE id = %s
            ''', [g.token['user']['id']])
            gh_api_token = user['github_api_token']

            headers = {
                "Authorization": "token " + gh_api_token,
                "User-Agent": "InfraBox"
            }
            url = '%s/repos/%s/%s/hooks/%s' % (os.environ['INFRABOX_GITHUB_API_URL'],
                                               gh_owner, gh_repo_name, gh_hook_id)

            # TODO(ib-steffen): allow custom ca bundles
            requests.delete(url, headers=headers, verify=False)

        # TODO: delete all tables
        g.db.execute('''
            DELETE FROM repository
            WHERE project_id = %s
        ''', [project_id])

        g.db.execute('''
            DELETE FROM collaborator
            WHERE project_id = %s
        ''', [project_id])

        g.db.commit()

        # Updated collaborator and project data will be pushed with next push cycle to Open Policy Agent

        return OK('deleted project')
