import os
import logging
import json

import requests
import psycopg2

from bottle import post, run, request, response

logging.basicConfig(
    format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%d-%m-%Y:%H:%M:%S',
    level=logging.DEBUG
)

LOGGER = logging.getLogger("github")

def get_env(name):
    if name not in os.environ:
        raise Exception("%s not set" % name)
    return os.environ[name]

def res(status, message):
    response.status = status
    return {"message": message}

def remove_ref(ref):
    return "/".join(ref.split("/")[2:])

def get_commits(url, token):
    headers = {
        "Authorization": "token " + token,
        "User-Agent": "InfraBox"
    },

    # TODO(ib-steffen): allow custom ca bundles
    return requests.get(url, headers, verify=False).json()


class Trigger(object):
    def __init__(self):
        self.conn = psycopg2.connect(dbname=os.environ['INFRABOX_DATABASE_DB'],
                                     user=os.environ['INFRABOX_DATABASE_USER'],
                                     password=os.environ['INFRABOX_DATABASE_PASSWORD'],
                                     host=os.environ['INFRABOX_DATABASE_HOST'],
                                     port=os.environ['INFRABOX_DATABASE_PORT'])

    def execute(self, stmt, args=None, fetch=True):
        cur = self.conn.cursor()
        cur.execute(stmt, args)

        if not fetch:
            cur.close()
            return None

        result = cur.fetchall()
        cur.close()
        return result

    def get_owner_token(self, repo_id):
        return self.execute('''
            SELECT github_api_token FROM "user" u
            INNER JOIN collaborator co
                ON co.user_id = u.id
                AND co.owner = true
            INNER JOIN project p
                ON co.project_id = p.id
            INNER JOIN repository r
                ON r.github_id = %s
                AND r.project_id = p.id
        ''', [repo_id])[0][0]

    def create_build(self, commit_id, project_id):
        build_no = self.execute('''
            SELECT count(distinct build_number) + 1 AS build_no
                          FROM build AS b
                          WHERE b.project_id = %s
        ''', [project_id])[0][0]

        result = self.execute('''
            INSERT INTO build (commit_id, build_number, project_id)
            VALUES (%s, %s, %s)
            RETURNING id
        ''', [commit_id, build_no, project_id])
        build_id = result[0][0]
        return build_id

    def create_job(self, commit_id, clone_url, build_id, project_id, github_private_repo, branch):
        git_repo = {
            "commit": commit_id,
            "clone_url": clone_url,
            "github_private_repo": github_private_repo,
            "branch": branch
        }

        self.execute('''
            INSERT INTO job (id, state, build_id, type,
                             name, project_id, build_only,
                             dockerfile, cpu, memory, repo)
            VALUES (gen_random_uuid(), 'queued', %s, 'create_job_matrix',
                    'Create Jobs', %s, false, '', 1, 1024, %s)
        ''', [build_id, project_id, json.dumps(git_repo)], fetch=False)


    def create_push(self, c, repository, branch, tag):
        if not c['distinct']:
            return

        result = self.execute('''
            SELECT id, project_id, private
            FROM repository
            WHERE github_id = %s''', [repository['id']])[0]

        repo_id = result[0]
        project_id = result[1]
        github_repo_private = result[2]
        commit_id = None

        result = self.execute('''
            SELECT id
            FROM "commit"
            WHERE id = %s
                AND project_id = %s
        ''', [c['id'], project_id])

        commit_id = c['id']

        if not result:
            status_url = repository['statuses_url'].format(sha=c['id'])
            result = self.execute('''
                INSERT INTO "commit" (
                    id, message, repository_id, timestamp,
                    author_name, author_email, author_username,
                    committer_name, committer_email, committer_username, url, branch, project_id,
                    tag, github_status_url)
                VALUES (%s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s)
                RETURNING id
            ''', [c['id'], c['message'], repo_id, c['timestamp'], c['author']['name'],
                  c['author']['email'], c['author']['username'], c['committer']['name'],
                  c['committer']['email'],
                  c['committer'].get('username', None), c['url'], branch, project_id, tag,
                  status_url])

        if tag:
            self.execute('''
                UPDATE "commit" SET tag = %s WHERE id = %s AND project_id = %s
            ''', [tag, c['id'], project_id], fetch=False)


        build_id = self.create_build(commit_id, project_id)
        self.create_job(c['id'], repository['clone_url'], build_id,
                        project_id, github_repo_private, branch)

    def handle_push(self, event):
        result = self.execute('''
            SELECT project_id FROM repository WHERE github_id = %s;
        ''', [event['repository']['id']])[0]

        project_id = result[0]

        result = self.execute('''
            SELECT build_on_push FROM project WHERE id = %s;
        ''', [project_id])[0]

        if not result[0]:
            return res(200, 'build_on_push not set')

        branch = None
        tag = None
        commits = []

        if event.get('base_ref', None):
            branch = remove_ref(event['base_ref'])

        ref = event['ref']
        if ref.startswith('refs/tags'):
            tag = remove_ref(ref)
            commits = [event['head_commit']]
        else:
            branch = remove_ref(ref)
            commits = event['commits']

        token = self.get_owner_token(event['repository']['id'])

        if not token:
            return res(200, 'no token')

        for commit in commits:
            self.create_push(commit, event['repository'], branch, tag)

        self.conn.commit()
        return res(200, 'ok')


    def handle_pull_request(self, event):
        if event['action'] == 'closed':
            return

        result = self.execute('''
            SELECT id, project_id, private FROM repository WHERE github_id = %s;
        ''', [event['repository']['id']])

        if not result:
            return res(404, "Unknown repository")

        repo_id = result[0]
        project_id = result[1]
        github_repo_private = result[2]

        result = self.execute('''
            SELECT build_on_push FROM project WHERE id = %s;
        ''', [project_id])[0]

        if not result[0]:
            return res(200, 'build_on_push not set')

        token = self.get_owner_token(event['repository']['id'])

        if not token:
            return res(200, 'no token')


        commits = get_commits(event['pull_request']['commits_url'], token)

        hc = None
        for commit in commits:
            if commit['sha'] == event['pull_request']['head']['sha']:
                hc = commit
                break

        if not hc:
            return res(500, 'Internal Server Error')

        result = self.execute('''
            SELECT id FROM pull_request WHERE project_id = %s and github_pull_request_id = %s
        ''', [repo_id, event['pull_request']['id']])

        if not result:
            result = self.execute('''
                INSERT INTO pull_request (project_id, github_pull_request_id,
                                         title, url)
                VALUES (%s, %s, %s, %s) RETURNING ID
            ''', [project_id,
                  event['pull_request']['id'],
                  event['pull_request']['title'],
                  event['pull_request']['html_url']
                 ])
            pr_id = result[0][0]

        result = self.execute('''
            SELECT id
            FROM "commit"
            WHERE id = %s
                AND project_id = %s
        ''', [hc['sha'], project_id])

        committer_login = None
        if hc.get('committer', None):
            committer_login = hc['committer']['login']

        branch = event['pull_request']['head']['ref']

        if not result:
            result = self.execute('''
                INSERT INTO "commit" (
                    id, message, repository_id, timestamp,
                    author_name, author_email, author_username,
                    committer_name, committer_email, committer_username, url, project_id,
                    branch, pull_request_id, github_status_url)
                VALUES (%s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s)
                RETURNING id
            ''', [hc['sha'], hc['commit']['message'],
                  repo_id, hc['commit']['author']['date'], hc['commit']['author']['name'],
                  hc['commit']['author']['email'], hc['author']['login'],
                  hc['commit']['committer']['name'],
                  hc['commit']['committer']['email'],
                  committer_login, hc['commit']['url'], project_id, branch, pr_id,
                  event['pull_request']['statuses_url']])
            commit_id = result[0][0]
        else:
            commit_id = result[0][0]

        build_id = self.create_build(commit_id, project_id)
        self.create_job(event['pull_request']['head']['sha'],
                        event['pull_request']['head']['repo']['clone_url'],
                        build_id, project_id, github_repo_private, branch)

        self.conn.commit()
        return res(200, 'ok')

@post('/api/v1/trigger')
def trigger_build():
    headers = dict(request.headers)

    if 'X-Github-Event' not in headers:
        return res(400, "X-Github-Event not set")

    event = headers['X-Github-Event']

    trigger = Trigger()
    if event == 'push':
        return trigger.handle_push(request.json)
    elif event == 'pull_request':
        return trigger.handle_pull_request(request.json)

    return res(200, "OK")

def main():
    get_env('INFRABOX_SERVICE')
    get_env('INFRABOX_VERSION')
    get_env('INFRABOX_DATABASE_DB')
    get_env('INFRABOX_DATABASE_USER')
    get_env('INFRABOX_DATABASE_PASSWORD')
    get_env('INFRABOX_DATABASE_HOST')
    get_env('INFRABOX_DATABASE_PORT')

    run(host='0.0.0.0', port=8083)

if __name__ == '__main__':
    main()
