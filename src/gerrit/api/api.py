import os
import json

import paramiko
from flask import Flask, request, Response, jsonify

app = Flask(__name__)

def get_env(name):
    if name not in os.environ:
        raise Exception("%s not set" % name)
    return os.environ[name]

def execute_ssh_cmd(client, cmd):
    _, stdout, stderr = client.exec_command(cmd)
    err = stderr.read()
    if err:
        print(err)

    return stdout.read()

def error(status, message):
    Response.status = status
    return {"message": message}

def get_branch(branch_or_sha, client, project):
    cmd = 'gerrit query --current-patch-set --format=JSON '
    cmd += 'status:merged project:%s limit:1' % project
    cmd += ' branch:%s' % branch_or_sha
    result = execute_ssh_cmd(client, cmd)

    rows = result.split("\n")
    if len(rows) <= 1:
        return None

    change = json.loads(rows[0])
    return change

def get_sha(branch_or_sha, client, project):
    cmd = 'gerrit query --current-patch-set --format=JSON '
    cmd += 'status:merged project:%s limit:1' % project
    cmd += ' %s' % branch_or_sha

    result = execute_ssh_cmd(client, cmd)

    rows = result.split("\n")
    if len(rows) <= 1:
        return None

    change = json.loads(rows[0])
    return change

@app.route('/api/v1/commit', methods=['POST'])
def get_commit():
    query = request.get_json()

    project = query.get('project', None)
    if not project:
        return error(400, "project not set")

    branch_or_sha = query.get('branch_or_sha', None)
    if not branch_or_sha:
        return error(400, "branch_or_sha not set")

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

    change = get_branch(branch_or_sha, client, project)
    branch = None
    if not change:
        change = get_sha(branch_or_sha, client, project)
    else:
        branch = branch_or_sha

    if not change:
        error(404, 'change not found')

    client.close()

    return jsonify({
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
    })

def main():
    get_env('INFRABOX_VERSION')
    get_env('INFRABOX_GERRIT_PORT')
    get_env('INFRABOX_GERRIT_HOSTNAME')
    get_env('INFRABOX_GERRIT_USERNAME')
    get_env('INFRABOX_GERRIT_KEY_FILENAME')

    app.run(host='0.0.0.0', port=8082)

if __name__ == '__main__':
    main()
