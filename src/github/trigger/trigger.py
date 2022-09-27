import json
import hashlib
import hmac
import re
from datetime import datetime

import eventlet
from eventlet import wsgi
eventlet.monkey_patch()

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from flask import request, g, jsonify
from pyinfraboxutils.ibflask import app

from pyinfraboxutils import get_env, get_logger
from pyinfraboxutils.db import connect_db

app.config['MAX_CONTENT_LENGHT'] = 10 * 1024 * 1024
app.config['OPA_ENABLED'] = False

logger = get_logger("github")

def res(status, message):
    return jsonify({"message": message}), status

def remove_ref(ref):
    return "/".join(ref.split("/")[2:])

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


def get_commits(url, token):
    headers = {
        "Authorization": "token " + token,
        "User-Agent": "InfraBox"
    }

    s = requests.Session()

    retries = Retry(total=5,
                    backoff_factor=0.1,
                    status_forcelist=[500, 502, 503, 504])

    s.mount('http://', HTTPAdapter(max_retries=retries))

    # TODO(ib-steffen): allow custom ca bundles
    r = requests.get(url + '?per_page=100', headers=headers, verify=False)
    result = []
    result.extend(r.json())

    p = get_next_page(r)
    while p:
        r = requests.get(p, headers=headers, verify=False)
        p = get_next_page(r)
        result.extend(r.json())

    return result


class Trigger(object):
    def execute(self, stmt, args=None, fetch=True):
        if fetch:
            return g.db.execute_many(stmt, args)

        return g.db.execute(stmt, args)

    def get_owner_token(self, repo_id):
        return self.execute('''
            SELECT github_api_token FROM "user" u
            INNER JOIN collaborator co
                ON co.user_id = u.id
                AND co.role = 'Owner'
            INNER JOIN project p
                ON co.project_id = p.id
            INNER JOIN repository r
                ON r.github_id = %s
                AND r.project_id = p.id
        ''', [repo_id])[0][0]

    def create_build(self, commit_id, project_id):
        build_no = self.execute('''
            SELECT max(build_number) + 1 AS build_no
            FROM build AS b
            WHERE b.project_id = %s
        ''', [project_id])[0][0]

        if not build_no:
            build_no = 1

        result = self.execute('''
            INSERT INTO build (commit_id, build_number, project_id)
            VALUES (%s, %s, %s)
            RETURNING id
        ''', [commit_id, build_no, project_id])
        build_id = result[0][0]
        return build_id

    def create_job(self, commit_id, clone_url, build_id, project_id, branch, env=None, fork=False):
        git_repo = {
            "commit": commit_id,
            "clone_url": clone_url,
            "branch": branch,
            "fork": fork
        }

        definition = {
            'build_only': False,
            'resources': {
                'limits': {
                    'cpu': 0.5,
                    'memory': 1024
                }
            }
        }

        self.execute('''
            INSERT INTO job (id, state, build_id, type,
                             name, project_id,
                             dockerfile, repo, env_var, cluster_name, definition)
            VALUES (gen_random_uuid(), 'queued', %s, 'create_job_matrix',
                    'Create Jobs', %s, '', %s, %s, null, %s)
        ''', [build_id, project_id, json.dumps(git_repo), env, json.dumps(definition)], fetch=False)

    def has_active_build(self, commit_id, project_id):
        result = self.execute('''
            SELECT count(*)
            FROM job
            JOIN build ON job.build_id = build.id
            JOIN "commit" ON build.commit_id = "commit".id and build.project_id = "commit".project_id
            LEFT JOIN "abort" ON "abort".job_id = job.id
            WHERE
                "commit".id = %s AND
                "commit".project_id = %s AND
                job.state IN ('running', 'queued', 'scheduled') AND
                "abort".job_id IS NULL
            GROUP BY job.state
        ''', [commit_id, project_id])

        if result:
            return True

        return False

    def create_push(self, c, repository, branch, tag):
        if not c['distinct']:
            return

        result = self.execute('''
            SELECT id, project_id
            FROM repository
            WHERE github_id = %s''', [repository['id']])[0]

        repo_id = result[0]
        project_id = result[1]
        commit_id = None

        result = self.execute('''
            SELECT id
            FROM "commit"
            WHERE id = %s
                AND project_id = %s
        ''', [c['id'], project_id])

        commit_id = c['id']
        if tag:
            self.execute('''
                UPDATE "commit" SET tag = %s WHERE id = %s AND project_id = %s
            ''', [tag, c['id'], project_id], fetch=False)

            build_on_tag = self.execute('''
                            SELECT build_on_tag
                            FROM project
                            WHERE id = %s''', [project_id])[0][0]

            if not build_on_tag and self.has_active_build(commit_id, project_id):
                return
        else:
            if self.has_active_build(commit_id, project_id):
                return

        if not result:
            status_url = repository['statuses_url'].format(sha=c['id'])
            self.execute('''
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
                ON CONFLICT DO NOTHING
            ''', [c['id'],
                  c['message'],
                  repo_id,
                  c['timestamp'],
                  c['author']['name'],
                  c['author']['email'],
                  c['author'].get('username', None),
                  c['committer']['name'],
                  c['committer']['email'],
                  c['committer'].get('username', None),
                  c['url'],
                  branch,
                  project_id,
                  tag,
                  status_url], fetch=False)

        build_id = self.create_build(commit_id, project_id)
        clone_url = repository['clone_url']

        if repository['private']:
            clone_url = repository['ssh_url']

        self.create_job(c['id'], clone_url, build_id,
                        project_id, branch)

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

        result = self.execute('''
            SELECT skip_pattern FROM project_skip_pattern WHERE project_id = %s;
        ''', [project_id])

        skip_pattern = None
        branch = None
        tag = None
        commit = None

        if result:
            skip_pattern = result[0][0]

        if event.get('base_ref', None):
            branch = remove_ref(event['base_ref'])

        ref = event['ref']
        if ref.startswith('refs/tags'):
            tag = remove_ref(ref)
            commit = event['head_commit']
        else:
            branch = remove_ref(ref)
            if event['commits']:
                commit = event['commits'][-1]

        token = self.get_owner_token(event['repository']['id'])

        if not token:
            return res(200, 'no token')

        if skip_pattern and re.search(skip_pattern, ref):
            return res(200, 'build_skip_pattern matched, skip this build')


        if commit:
            self.create_push(commit, event['repository'], branch, tag)

        g.db.commit()
        return res(200, 'ok')


    def handle_pull_request(self, event):
        if event['action'] not in ['opened', 'reopened', 'synchronize']:
            return res(200, 'action ignored')

        result = self.execute('''
            SELECT id, project_id FROM repository WHERE github_id = %s;
        ''', [event['repository']['id']])

        if not result:
            return res(404, "Unknown repository")

        result = result[0]

        repo_id = result[0]
        project_id = result[1]

        result = self.execute('''
            SELECT build_on_push FROM project WHERE id = %s;
        ''', [project_id])[0]

        if not result[0]:
            return res(200, 'build_on_push not set')

        token = self.get_owner_token(event['repository']['id'])

        if not token:
            return res(200, 'no token')


        for _ in range(0, 3):
            commits = get_commits(event['pull_request']['commits_url'], token)
            hc = None
            for commit in commits:
                if commit['sha'] == event['pull_request']['head']['sha']:
                    hc = commit
                    break

            if not hc:
                # We might receive the pr event before the push event.
                # this may lead to a situation that we cannot yet
                # find the actual commit. Wait some time and retry.
                eventlet.sleep(1)

        if not hc:
            logger.error('Head commit not found: %s', event['pull_request']['head']['sha'])
            return res(500, 'Internal Server Error')

        is_fork = event['pull_request']['head']['repo']['fork']

        result = self.execute('''
            SELECT id FROM pull_request WHERE project_id = %s and github_pull_request_id = %s
        ''', [project_id, event['pull_request']['id']])

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
        else:
            pr_id = result[0][0]

        committer_login = None
        if hc.get('committer', None):
            committer_login = hc['committer']['login']

        branch = event['pull_request']['head']['ref']

        def getLabelsName(event):
            names = []
            for label in event['pull_request']['labels']:
                for k,v in label.items():
                    if k == 'name':
                        names.append(v)
                        break
            return ','.join(names)

        author_email = 'unknown'
        author_login = 'unknown'
        author_name = 'unknown'
        author_date = None

        if hc['commit'].get('author', None):
            author = hc['commit']['author']
            author_email = author.get('email', 'unknown')
            author_login = author.get('login', 'unknown')
            author_name = author.get('name', 'unknown')
            author_date = author.get('date', datetime.now())

        env = json.dumps({
            "GITHUB_PULL_REQUEST_NUMBER": event['pull_request']['number'],
            "GITHUB_PULL_REQUEST_BASE_LABEL": event['pull_request']['base']['label'],
            "GITHUB_PULL_REQUEST_BASE_REF": event['pull_request']['base']['ref'],
            "GITHUB_PULL_REQUEST_BASE_SHA": event['pull_request']['base']['sha'],
            "GITHUB_PULL_REQUEST_BASE_REPO_CLONE_URL": event['pull_request']['base']['repo']['clone_url'],
            "GITHUB_REPOSITORY_FULL_NAME": event['repository']['full_name'],
            "GITHUB_PULL_REQUEST_LABELS": getLabelsName(event),
            "GITHUB_PULL_REQUEST_DRAFT": event['pull_request']['draft'],
            "COMMIT_AUTHOR_NAME": author_name
        })
        commit_id = hc['sha']

        self.execute('''
            INSERT INTO "commit" (
                id, message, repository_id, timestamp,
                author_name, author_email, author_username,
                committer_name, committer_email, committer_username, url, project_id,
                branch, pull_request_id, github_status_url, env)
            VALUES (%s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s)
            ON CONFLICT ON CONSTRAINT commit_pkey DO UPDATE
                SET pull_request_id = %s, env = %s
        ''', [hc['sha'], hc['commit']['message'],
              repo_id, author_date, author_name,
              author_email, author_login,
              hc['commit']['committer']['name'],
              hc['commit']['committer']['email'],
              committer_login, hc['html_url'], project_id, branch, pr_id,
              event['pull_request']['statuses_url'], env, pr_id, env], fetch=False)

        # Abort jobs which are still running on the same PR
        self.execute('''
            INSERT INTO abort
            SELECT j.id, null
            FROM job j
            JOIN build b
            ON b.id = j.build_id
            JOIN commit c
            ON b.commit_id = c.id
            AND b.project_id = c.project_id
            WHERE
                c.pull_request_id = %s AND
                j.state in ('scheduled', 'running', 'queued') AND
                c.id != %s
        ''', [pr_id, commit_id], fetch=False)

        if event['action'] in ['opened', 'reopened']:
            self.execute('''
            INSERT INTO abort
            SELECT j.id, null
            FROM job j
            JOIN build b
            ON b.id = j.build_id
            WHERE
                b.commit_id = %s AND
                j.state in ('scheduled', 'running', 'queued')
            ''', [commit_id], fetch=False)

        if not self.has_active_build(commit_id, project_id):
            build_id = self.create_build(commit_id, project_id)
            clone_url = event['repository']['clone_url']

            if event['repository']['private']:
                clone_url = event['repository']['ssh_url']

            self.create_job(event['pull_request']['head']['sha'],
                            clone_url,
                            build_id, project_id, None, env=env, fork=is_fork)

        g.db.commit()
        return res(200, 'ok')


def sign_blob(key, blob):
    return 'sha1=' + hmac.new(key, blob, hashlib.sha1).hexdigest()

@app.route('/github/hook', methods=['POST'])
def trigger_build():
    headers = dict(request.headers)

    if 'X-Github-Event' not in headers:
        return res(400, "X-Github-Event not set")

    if 'X-Hub-Signature' not in headers:
        return res(400, "X-Hub-Signature not set")

    event = headers['X-Github-Event']
    sig = headers['X-Hub-Signature']
    #pylint: disable=no-member
    body = request.get_data()
    secret = get_env('INFRABOX_GITHUB_WEBHOOK_SECRET')
    signed = sign_blob(secret, body)

    if signed != sig:
        return res(400, "X-Hub-Signature does not match blob signature")

    trigger = Trigger()
    if event == 'push':
        # delay push event in case push and pr event comes at the same time
        eventlet.sleep(7)
        return trigger.handle_push(request.get_json())
    elif event == 'pull_request':
        return trigger.handle_pull_request(request.get_json())

    return res(200, "OK")

@app.route('/ping', methods=['GET'])
def ping():
    return res(200, "OK")

def main():
    get_env('INFRABOX_VERSION')
    get_env('INFRABOX_DATABASE_DB')
    get_env('INFRABOX_DATABASE_USER')
    get_env('INFRABOX_DATABASE_PASSWORD')
    get_env('INFRABOX_DATABASE_HOST')
    get_env('INFRABOX_DATABASE_PORT')
    get_env('INFRABOX_GITHUB_WEBHOOK_SECRET')

    connect_db() # Wait until DB is ready

    wsgi.server(eventlet.listen(('0.0.0.0', 8080)), app)

if __name__ == '__main__':
    main()
