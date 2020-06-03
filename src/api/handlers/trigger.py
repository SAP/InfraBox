import os
import json
import datetime
import requests

from flask_restx import Resource, fields
from flask import abort, request, g

from pyinfraboxutils.ibflask import OK
from pyinfraboxutils.ibrestplus import api, response_model

ns = api.namespace('Projects',
                   path='/api/v1/projects/<project_id>',
                   description='Project related operations')

def execute_github_api(url, token):
    headers = {
        "Authorization": "token " + token,
        "User-Agent": "InfraBox"
    }

    # TODO(ib-steffen): allow custom ca bundles
    url = os.environ['INFRABOX_GITHUB_API_URL'] + url
    return requests.get(url, headers=headers, verify=False)

def get_sha_for_branch(owner, repo, branch_or_sha, token):
    url = '/repos/%s/%s/branches/%s' % (owner, repo, branch_or_sha)
    result = execute_github_api(url, token)

    if result.status_code != 200:
        return None

    result = result.json()

    if not result:
        return None

    sha = result['commit']['sha']
    return sha

def get_github_commit(owner, token, repo, branch_or_sha, branch):
    # Check if it's a branch
    sha = get_sha_for_branch(owner, repo, branch_or_sha, token)

    if sha:
        branch = branch_or_sha
    else:
        sha = branch_or_sha

    url = '/repos/%s/%s/commits/%s' % (owner, repo, sha)
    result = execute_github_api(url, token)

    if result.status_code != 200:
        return abort(404, "sha '%s' not found" % sha)

    result = result.json()

    return {
        "sha": result['sha'],
        "branch": branch,
        "url": result['html_url'],
        "author": {
            "name": result['commit']['author']['name'],
            "email": result['commit']['author']['email']
        },
        "message": result['commit']['message']
    }


def insert_commit(project_id, repo_id, commit):
    commits = g.db.execute_many('''
        SELECT * FROM "commit"
        WHERE id = %s AND project_id = %s
    ''', [commit['sha'], project_id])

    if commits:
        return

    g.db.execute('''
        INSERT INTO "commit" (
            id,
            message,
            repository_id,
            timestamp,
            author_name,
            author_email,
            author_username,
            committer_name,
            committer_email,
            committer_username,
            url,
            branch,
            project_id,
            tag)
        VALUES (%s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s)
    ''', [commit['sha'],
          commit['message'],
          repo_id,
          datetime.datetime.now(),
          commit['author']['name'],
          commit['author']['email'],
          '', '', '', '',
          commit['url'],
          commit['branch'],
          project_id,
          None
         ])

def create_github_commit(project_id, repo_id, branch_or_sha, branch):
    r = g.db.execute_one('''
        SELECT github_owner, name
        FROM repository
        WHERE id = %s
    ''', [repo_id])

    github_owner = r[0]
    repo_name = r[1]

    u = g.db.execute_one('''
        SELECT github_api_token FROM "user" u
        INNER JOIN collaborator co
            ON co.user_id = u.id
            AND co.role = 'Owner'
        INNER JOIN project p
            ON co.project_id = p.id
        INNER JOIN repository r
            ON r.id = %s
            AND r.project_id = p.id
    ''', [repo_id])
    github_api_token = u[0]

    commit = get_github_commit(github_owner, github_api_token, repo_name, branch_or_sha, branch)

    insert_commit(project_id, repo_id, commit)
    return commit

def create_gerrit_commit(project_id, repo_id, branch_or_sha):
    r = g.db.execute_one('''
        SELECT name
        FROM repository
        WHERE id = %s
    ''', [repo_id])

    repo_name = r[0]

    data = {
        'branch_or_sha': branch_or_sha,
        'project': repo_name
    }
    r = requests.post('http://localhost:8082/api/v1/commit', json=data)
    commit = r.json()

    if r.status_code != 200:
        abort(r.status_code, commit['message'])

    insert_commit(project_id, repo_id, commit)
    return commit

def create_git_job(commit, build_no, project_id, repo, project_type, env, infrabox_file):
    build = g.db.execute_one('''
        INSERT INTO build (commit_id, build_number, project_id)
        VALUES (%s, %s, %s)
        RETURNING *
    ''', [commit['sha'], build_no, project_id])

    git_repo = {
        'commit': commit['sha'],
        'clone_url': commit.get('clone_url', repo['clone_url']),
        'clone_all': True
    }

    if project_type == 'github':
        git_repo['github_private_repo'] = repo['private']

    env_var = None
    if env:
        env_var = {}
        for e in env:
            env_var[e['name']] = e['value']

    definition = {
        'build_only': False,
        'infrabox_file': infrabox_file,
        'resources': {
            'limits': {
                'memory': 1024,
                'cpu': 0.5
            }
        }
    }

    g.db.execute('''
        INSERT INTO job (id, state, build_id, type, name, project_id,
                         dockerfile, repo, env_var, cluster_name, definition)
        VALUES (gen_random_uuid(), 'queued', %s, 'create_job_matrix',
                'Create Jobs', %s, '', %s, %s, %s, %s)
    ''', [build['id'], project_id, json.dumps(git_repo), json.dumps(env_var), None, json.dumps(definition)])

    return (build['id'], build['build_number'])


def create_upload_job(project_id, build_no, env, infrabox_file):
    last_build = g.db.execute_one('''
        SELECT source_upload_id
        FROM build
        WHERE project_id = %s
        ORDER BY build_number DESC
        LIMIT 1
    ''', [project_id])

    if not last_build:
        abort(400, 'no build yet')

    upload_id = last_build[0]

    build = g.db.execute_one('''
        INSERT INTO build (source_upload_id, build_number, project_id)
        VALUES (%s, %s, %s)
        RETURNING *
    ''', [upload_id, build_no, project_id])

    env_var = None
    if env:
        env_var = {}
        for e in env:
            env_var[e['name']] = e['value']

    definition = {
        'build_only': False,
        'infrabox_file': infrabox_file,
        'resources': {
            'limits': {
                'memory': 1024,
                'cpu': 0.5
            }
        }
    }

    g.db.execute('''
        INSERT INTO job (id, state, build_id, type, name, project_id,
                         dockerfile, env_var, definition)
        VALUES (gen_random_uuid(), 'queued', %s, 'create_job_matrix',
                'Create Jobs', %s, '', %s, %s)
    ''', [build['id'], project_id, json.dumps(env_var), json.dumps(definition)])

    return (build['id'], build['build_number'])

env_model = api.model('EnvVar', {
    'name': fields.String(required=True, description='Name'),
    'value': fields.String(required=True, description='Value')
})

trigger_model = api.model('Trigger', {
    'branch_or_sha': fields.String(required=True, description='Branch or sha'),
    'env': fields.List(fields.Nested(env_model)),
    'branch': fields.String(description='branch if sha submitted (GitHub only)')
})

def trigger_build(project_id):
    body = request.get_json()
    branch_or_sha = body.get('branch_or_sha', None)
    infrabox_file = body.get('infrabox_file', 'infrabox.json')
    env = body.get('env', None)
    branch = body.get('branch', None)

    project = g.db.execute_one('''
        SELECT type
        FROM project
        WHERE id = %s
    ''', [project_id])

    if not project:
        abort(404, 'project not found')

    project_type = project[0]

    r = g.db.execute_one('''
        SELECT max(build_number) + 1 AS build_no
        FROM build AS b
        WHERE b.project_id = %s
    ''', [project_id])
    build_no = r[0]

    if not build_no:
        build_no = 1

    new_build_id = None
    new_build_number = None

    if project_type in ('gerrit', 'github'):
        repo = g.db.execute_one('''
            SELECT id, name, clone_url, private
            FROM repository
            WHERE project_id = %s
        ''', [project_id])

        if not repo:
            abort(404, 'repo not found')

        repo_id = repo[0]

        if project_type == 'github':
            commit = create_github_commit(project_id, repo_id, branch_or_sha, branch)
            (new_build_id, new_build_number) = create_git_job(commit,
                                                              build_no,
                                                              project_id,
                                                              repo,
                                                              project_type,
                                                              env,
                                                              infrabox_file)
        elif project_type == 'gerrit':
            commit = create_gerrit_commit(project_id, repo_id, branch_or_sha)
            (new_build_id, new_build_number) = create_git_job(commit,
                                                              build_no,
                                                              project_id,
                                                              repo,
                                                              project_type,
                                                              env,
                                                              infrabox_file)
    elif project_type == 'upload':
        (new_build_id, new_build_number) = create_upload_job(project_id, build_no, env, infrabox_file)
    else:
        abort(404)

    g.db.commit()

    data = {
        'build': {
            'id': new_build_id,
            'build_number': new_build_number,
            'restartCounter': 1
        }
    }

    return OK('Build triggered', data)

@ns.route('/trigger')
@api.response(403, 'Not Authorized')
@api.response(404, 'Project not found')
class Trigger(Resource):

    @api.expect(trigger_model)
    @api.response(200, 'Success', response_model)
    def post(self, project_id):
        '''
        Trigger a new build
        '''
        return trigger_build(project_id)
