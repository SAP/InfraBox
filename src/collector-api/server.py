#pylint: disable=unused-import,relative-import,wrong-import-position
import uuid
import os
import sys
import json

from flask import Flask, request, send_from_directory, abort, Response
from flask_restx import Resource, Api

import eventlet
eventlet.monkey_patch()
reload(sys)
sys.setdefaultencoding('utf8')

from pyinfraboxutils import get_logger

logger = get_logger('api')

storage_path = '/tmp/collector/'

app = Flask(__name__)
app.config['OPA_ENABLED'] = False
api = Api(app)


@api.route('/ping')
class Ping(Resource):
    def get(self):
        return {'status': 200}

def handle_entry(entry):
    if 'kubernetes' not in entry:
        return

    e = entry['kubernetes']
    pod_path = os.path.join(storage_path, e['pod_id'])

    if not os.path.exists(pod_path):
        os.makedirs(pod_path)

    metadata_path = os.path.join(pod_path, "metadata.json")
    container_name = e['container_name']
    if '/' in container_name:
        container_name = container_name.split("/")[-1]
    log_path = os.path.join(pod_path, container_name +".log")

    if not os.path.exists(metadata_path):
        with open(metadata_path, 'w+') as metadata_file:
            md = {
                'namespace_name': e['namespace_name'],
                'pod_id': e['pod_id'],
                'pod_name': e['pod_name'],
                'containers': []
            }
            json.dump(md, metadata_file)

    if not os.path.exists(log_path):
        # this is the first log entry we receive, so also register it in the metadata
        with open(metadata_path, 'r') as metadata_file:
            md = json.load(metadata_file)
            md['containers'].append(e['container_name'])

        with open(metadata_path, 'w') as metadata_file:
            json.dump(md, metadata_file)

    if 'log' in entry:
        with open(log_path, 'a+') as log_file:
            log = entry['log']
            log = log.replace('\x00', '\n')
            if not log.endswith('\n'):
                log = log + '\n'
            log_file.write(log)

@api.route('/api/log')
class Console(Resource):
    def post(self):
        entries = request.get_json()

        for e in entries:
            handle_entry(e)

        return {'status': 200}

@api.route('/api/pods')
class Pods(Resource):
    def get(self):
        pods = []
        for root, dirs, _ in os.walk(storage_path):
            for name in dirs:
                p = os.path.join(root, name, 'metadata.json')
                with open(p) as f:
                    pods.append(json.load(f))

        return pods

@api.route('/api/pods/<pod_id>')
class Pod(Resource):
    def get(self, pod_id):
        p = os.path.join(os.path.join(storage_path), pod_id, 'metadata.json')

        if not p.startswith(storage_path):
            abort(404)

        if not os.path.exists(p):
            abort(404)

        with open(p) as f:
            return json.load(f)

@api.route('/api/pods/<pod_id>/log/<container_name>')
class PodLog(Resource):
    def get(self, pod_id, container_name):
        p = os.path.join(os.path.join(storage_path), pod_id, container_name + '.log')

        if not p.startswith(storage_path):
            abort(404)

        if not os.path.exists(p):
            abort(404)

        with open(p) as f:
            d = f.read()
            return Response(d, mimetype='text/plain')

def main(): # pragma: no cover
    app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024 * 4

    if not os.path.exists(storage_path):
        os.makedirs(storage_path)

    port = int(os.environ.get('INFRABOX_PORT', 8080))
    logger.info('Starting Server on port %s', port)
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__": # pragma: no cover
    main()
