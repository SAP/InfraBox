import os
import requests

from flask import g, abort, request
from flask_restplus import Resource, fields

from pyinfraboxutils import get_logger
from pyinfrabox.utils import validate_uuid4
from pyinfraboxutils.ibrestplus import api
from pyinfraboxutils.ibflask import auth_required, OK

from api.namespaces import project as ns


logger = get_logger('project')

project_model = api.model('Project', {
    'id': fields.String(required=True),
    'name': fields.String(required=True),
    'type': fields.String(required=True),
    'public': fields.String(required=True)
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

add_project_model = ns.schema_model('AddProject', add_project_schema)

if os.environ['INFRABOX_HA_ENABLED'] == 'true':
    webhook_root_url = os.environ['INFRABOX_HA_ROOT_URL']
else:
    webhook_root_url = os.environ['INFRABOX_ROOT_URL']

@ns.route('/')
class Projects(Resource):

    @auth_required(['user'], check_project_access=False)
    @api.marshal_list_with(project_model)
    def get(self):
        projects = g.db.execute_many_dict("""
            SELECT p.id, p.name, p.type, p.public
            FROM project p
            INNER JOIN collaborator co
            ON co.project_id = p.id
            AND %s = co.user_id
            ORDER BY p.name
        """, [g.token['user']['id']])

        return projects

    @auth_required(['user'], check_project_access=False)
    @api.expect(add_project_model)
    def post(self):
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

        if projects['cnt'] > 50:
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
            INSERT INTO collaborator (user_id, project_id, owner)
            VALUES (%s, %s, true)
        ''', [user_id, project_id])


        if typ == 'github':
            split = github_repo_name.split('/')
            owner = split[0]
            repo_name = split[1]

            g.db.execute('''
                INSERT INTO repository (name, html_url, clone_url, github_id,
                                        private, project_id, github_owner)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', [repo['name'], repo['html_url'], repo['clone_url'],
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
                    'url': webhook_root_url + '/github/hook',
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
        elif typ == 'gerrit':
            g.db.execute('''
                INSERT INTO repository (name, private, project_id, html_url, clone_url, github_id)
                VALUES (%s, false, %s, '', '', 0)
            ''', [name, project_id])

        g.db.commit()

        return OK('Project added')

@ns.route('/name/<project_name>')
class ProjectName(Resource):

    @auth_required(['user'], check_project_access=False, allow_if_public=True)
    @api.marshal_with(project_model)
    def get(self, project_name):
        project = g.db.execute_one_dict('''
            SELECT id, name, type, public
            FROM project
            WHERE name = %s
        ''', [project_name])

        if not project:
            abort(404)

        return project


@ns.route('/<project_id>/')
class Project(Resource):

    @auth_required(['user'], allow_if_public=True)
    @api.marshal_with(project_model)
    def get(self, project_id):
        project = g.db.execute_one_dict('''
            SELECT p.id, p.name, p.type, p.public
            FROM project p
            WHERE id = %s
        ''', [project_id])

        return project

    @auth_required(['user'], check_project_owner=True)
    def delete(self, project_id):
        if not validate_uuid4(project_id):
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

        return OK('deleted project')
