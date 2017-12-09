import json
import datetime
import jsonschema
import requests

from flask import abort, request, g
from pyinfraboxutils.ibflask import app, auth_token_required, OK

def validate(data, schema):
    try:
        jsonschema.validate(data, schema)
    except Exception as e:
        abort(400, str(e))

def validate_body(schema):
    body = request.get_json()
    validate(body, schema)
    return body

def insert_commit(project_id, repo_id, branch, commit):
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
          branch,
          project_id,
          None
         ])

def create_github_commit(project_id, repo_id, sha, branch):
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
            AND co.owner = true
        INNER JOIN project p
            ON co.project_id = p.id
        INNER JOIN repository r
            ON r.id = %s
            AND r.project_id = p.id
    ''', [repo_id])
    github_api_token = u[0]

    data = {
        'sha': sha,
        'branch': branch,
        'owner': github_owner,
        'repo': repo_name,
        'token': github_api_token
    }

    r = requests.post('http://localhost:8081/api/v1/commit', data=data)
    commit = r.json()

    insert_commit(project_id, repo_id, branch, commit)
    return commit

def create_gerrit_commit(project_id, repo_id, sha, branch):
    r = g.db.execute_one('''
        SELECT name
        FROM repository
        WHERE id = %s
    ''', [repo_id])

    repo_name = r[0]

    data = {
        'sha': sha,
        'branch': branch,
        'project': repo_name
    }
    r = requests.post('http://localhost:8082/api/v1/commit', json=data)
    commit = r.json()
    insert_commit(project_id, repo_id, branch, commit)
    return commit

def create_git_job(commit, build_no, project_id, repo):
    build = g.db.execute_one('''
        INSERT INTO build (commit_id, build_number, project_id)
        VALUES (%s, %s, %s)
        RETURNING *
    ''', [commit['sha'], build_no, project_id])

    git_repo = {
        'commit': commit['sha'],
        'clone_url': repo['clone_url']
    }

    if 'clone_url' in commit:
        git_repo['clone_url'] = commit['clone_url']

    g.db.execute('''
        INSERT INTO job (id, state, build_id, type, name, project_id,
                         build_only, dockerfile, cpu, memory, repo)
        VALUES (gen_random_uuid(), 'queued', %s, 'create_job_matrix',
                'Create Jobs', %s, false, '', 1, 1024, %s)
    ''', [build['id'], project_id, json.dumps(git_repo)])


def create_upload_job(project_id, build_no):
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

    g.db.execute('''
        INSERT INTO job (id, state, build_id, type, name, project_id,
                         build_only, dockerfile, cpu, memory)
        VALUES (gen_random_uuid(), 'queued', %s, 'create_job_matrix',
                'Create Jobs', %s, false, '', 1, 1024)
    ''', [build['id'], project_id])



@app.route('/api/v1/project/<project_id>/trigger', methods=['POST'])
@auth_token_required(['user', 'project'])
def trigger_build(project_id):
    TriggerSchema = {
        'id': '/TriggerSchema',
        'type': 'object',
        'properties': {
            'branch': {'type': 'string'},
            'sha': {'type': 'string'},
        }
    }

    body = validate_body(TriggerSchema)
    branch = body.get('branch', None)
    sha = body.get('sha', None)

    project = g.db.execute_one('''
        SELECT type
        FROM project
        WHERE id = %s
    ''', [project_id])

    if not project:
        abort(404, 'project not found')

    project_type = project[0]

    r = g.db.execute_one('''
        SELECT count(distinct build_number) + 1 AS build_no
        FROM build AS b
        WHERE b.project_id = %s
    ''', [project_id])
    build_no = r[0]

    if project_type in ('gerrit', 'github'):
        repo = g.db.execute_one('''
            SELECT id, name, clone_url
            FROM repository
            WHERE project_id = %s
        ''', [project_id])

        if not repo:
            abort(404, 'repo not found')

        repo_id = repo[0]

        if project_type == 'github':
            commit = create_github_commit(project_id, repo_id, sha, branch)
            create_git_job(commit, build_no, project_id, repo)
        elif project_type == 'gerrit':
            commit = create_gerrit_commit(project_id, repo_id, sha, branch)
            create_git_job(commit, build_no, project_id, repo)
    elif project_type == 'upload':
        create_upload_job(project_id, build_no)
    else:
        abort(404)

    g.db.commit()
    return OK('build triggered')
