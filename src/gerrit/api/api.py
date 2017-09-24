import os
import json

import paramiko
from bottle import post, run, request, response

def get_env(name):
    if name not in os.environ:
        raise Exception("%s not set" % name)
    return os.environ[name]

def execute_ssh_cmd(client, cmd):
    _, stdout, stderr = client.exec_command(cmd)
    err = stderr.read()
    if err:
        print err

    return stdout.read()

def error(status, message):
    response.status = status
    return {"message": message}

@post('/api/v1/commit')
def get_commit():
    query = dict(request.forms)

    if 'project' not in query:
        return error(400, "project not set")

    if 'branch' not in query and 'sha' not in query:
        return error(400, "either branch or sha must be set")

    project = query['project']
    branch = query.get('branch', None)
    sha = query.get('sha', None)

    gerrit_port = int(get_env('INFRABOX_GERRIT_PORT'))
    gerrit_hostname = get_env('INFRABOX_GERRIT_HOSTNAME')
    gerrit_username = get_env('INFRABOX_GERRIT_USERNAME')
    gerrit_key_filename = get_env('INFRABOX_GERRIT_KEY_FILENAME')

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(username=gerrit_username,
                   hostname=gerrit_hostname,
                   port=gerrit_port,
                   key_filename=gerrit_key_filename)
    client.get_transport().set_keepalive(60)
    cmd = 'gerrit query --current-patch-set --format=JSON '
    cmd += 'status:merged project:%s limit:1' % project

    if branch:
        cmd += ' branch:%s' % branch

    if sha:
        cmd += ' %s' % sha

    result = execute_ssh_cmd(client, cmd)
    client.close()

    rows = result.split("\n")
    if len(rows) <= 1:
        return error(400, "change not found")

    change = json.loads(rows[0])

    return {
        "sha": change['currentPatchSet']['revision'],
        "branch": branch,
        "url": change['url'],
        "clone_url": "ssh://%s@%s:%s/%s" % (get_env('INFRABOX_GERRIT_USERNAME'),
                                            get_env('INFRABOX_GERRIT_HOSTNAME'),
                                            get_env('INFRABOX_GERRIT_PORT'),
                                            project),
        "author": {
            "name": change['owner']['name'],
            "email": change['owner']['email']
        },
        "message": change['commitMessage']
    }

def main():
    get_env('INFRABOX_SERVICE')
    get_env('INFRABOX_VERSION')
    get_env('INFRABOX_GERRIT_PORT')
    get_env('INFRABOX_GERRIT_HOSTNAME')
    get_env('INFRABOX_GERRIT_USERNAME')
    get_env('INFRABOX_GERRIT_KEY_FILENAME')

    run(host='0.0.0.0', port=8082)

if __name__ == '__main__':
    main()
