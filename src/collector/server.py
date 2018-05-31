#pylint: disable=unused-import,relative-import,wrong-import-position
import uuid
import os
import sys
import json

from flask import Flask, request, send_from_directory, abort, Response
from flask_restplus import Resource, Api

import eventlet
eventlet.monkey_patch()

from pyinfraboxutils import get_env, print_stackdriver, get_logger

logger = get_logger('api')

storage_path = '/tmp/collector/'

app = Flask(__name__)
api = Api(app)

@api.route('/ping')
class Ping(Resource):
    def get(self):
        return {'status': 200}

def handle_entry(entry):
    e = entry['kubernetes']
    pod_path = os.path.join(storage_path, e['pod_id'])

    if not os.path.exists(pod_path):
        os.makedirs(pod_path)

    metadata_path = os.path.join(pod_path, "metadata.json")
    log_path = os.path.join(pod_path, e['container_name'] +".log")


    if not os.path.exists(metadata_path):
        with open(metadata_path, 'w+') as metadata_file:
            md = {
                'namespace_id': e['namespace_id'],
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
            log_file.write(entry['log'])

@api.route('/api/console')
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

        logger.error(p)

        if not p.startswith(storage_path):
            logger.error('not start')
            abort(404)

        if not os.path.exists(p):
            logger.error('exists')
            abort(404)

        with open(p) as f:
            d = f.read()
            logger.error(d)
            return Response(d, mimetype='text/plain')

def main(): # pragma: no cover
    app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024 * 4

    port = int(os.environ.get('INFRABOX_PORT', 8080))
    logger.info('Starting Server on port %s', port)
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__": # pragma: no cover
    main()
