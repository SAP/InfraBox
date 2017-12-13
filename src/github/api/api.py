import os
import logging

import requests
from bottle import post, run, request, response

logging.basicConfig(
    format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%d-%m-%Y:%H:%M:%S',
    level=logging.DEBUG
)

logger = logging.getLogger("github")

def get_env(name): # pragma: no cover
    if name not in os.environ:
        raise Exception("%s not set" % name)
    return os.environ[name]

def execute_api(url, token):
    headers = {
        "Authorization": "token " + token,
        "User-Agent": "InfraBox"
    }

    # TODO(ib-steffen): allow custom ca bundles
    url = get_env('INFRABOX_GITHUB_API_URL') + url
    return requests.get(url, headers=headers, verify=False)

def error(status, message):
    response.status = status
    return {"message": message}

def get_sha_for_branch(owner, repo, branch_or_sha, token):
    url = '/repos/%s/%s/branches/%s' % (owner, repo, branch_or_sha)
    result = execute_api(url, token)

    if result.status_code != 200:
        return None

    result = result.json()

    if not result:
        return None

    sha = result['commit']['sha']
    return sha

@post('/api/v1/commit')
def get_commit():
    query = dict(request.forms)

    owner = query.get('owner', None)
    if not owner:
        return error(400, "owner not set")

    token = query.get('token', None)
    if not token:
        return error(400, "token not set")

    repo = query.get('repo', None)
    if not repo:
        return error(400, "repo not set")

    branch_or_sha = query.get('branch_or_sha', None)

    if not branch_or_sha:
        return error(400, "branch_or_sha not set")

    # Check if it's a branch
    sha = get_sha_for_branch(owner, repo, branch_or_sha, token)

    branch = None
    if sha:
        branch = branch_or_sha
    else:
        sha = branch_or_sha

    url = '/repos/%s/%s/commits/%s' % (owner, repo, sha)
    result = execute_api(url, token)

    if result.status_code != 200:
        return error(404, "sha '%s' not found" % sha)

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

def main(): # pragma: no cover
    get_env('INFRABOX_SERVICE')
    get_env('INFRABOX_VERSION')
    get_env('INFRABOX_GITHUB_API_URL')

    run(host='0.0.0.0', port=8081)

if __name__ == '__main__': # pragma: no cover
    main()
