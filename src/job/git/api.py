#pylint: disable=wrong-import-position
import subprocess
import os
import traceback

from gevent.wsgi import WSGIServer

from flask import Flask, request
from flask_restplus import Api, Resource, fields

from pyinfraboxutils import print_stackdriver, get_logger

app = Flask(__name__)
api = Api(app)

logger = get_logger('api')
ns = api.namespace('/', description='Clone repo')

@ns.route('/ping')
class Ping(Resource):
    def get(self):
        return {'status': 200}

clone_model = api.model('Clone', {
    'commit': fields.String(required=True, description='Commit'),
    'clone_url': fields.String(required=True, description='Clone URL'),
    'branch': fields.String(required=False, description='Branch'),
    'ref': fields.String(required=False, description='Ref'),
    'clone_all': fields.Boolean(required=False, description='Clone all'),
    'sub_path': fields.String(required=False, description='Sub path'),
    'submodules': fields.String(required=False, description='Init submodules')
})

@ns.route('/clone_repo')
class Clone(Resource):
    def execute(self, args, cwd=None):
        output = '\n'
        output += ' '.join(args)
        output += '\n'
        output += subprocess.check_output(args, cwd=cwd, stderr=subprocess.STDOUT)
        return output

    @api.expect(clone_model)
    def post(self):
        try:
            output = ""
            mount_repo_dir = os.environ.get('INFRABOX_JOB_REPO_MOUNT_PATH', '/repo')

            body = request.get_json()
            commit = body['commit']
            clone_url = body['clone_url']
            branch = body.get('branch', None)
            ref = body.get('ref', None)
            clone_all = body.get('clone_all', False)
            sub_path = body.get('sub_path', None)
            submodules = body.get('submodules', True)

            if sub_path:
                mount_repo_dir = os.path.join(mount_repo_dir, sub_path)

            if os.environ['INFRABOX_GENERAL_DONT_CHECK_CERTIFICATES'] == 'true':
                output += self.execute(('git', 'config', '--global', 'http.sslVerify', 'false'))

            cmd = ['git', 'clone']

            if not clone_all:
                cmd += ['--depth=10']

                if branch:
                    cmd += ['--single-branch', '-b', branch]

            cmd += [clone_url, mount_repo_dir]

            exc = None
            for _ in range(0, 2):
                exc = None
                try:
                    output += self.execute(cmd)
                    break
                except Exception as e:
                    exc = e

            if exc:
                raise exc

            if ref:
                cmd = ['git', 'fetch', '--depth=10', clone_url, ref]
                output += self.execute(cmd, cwd=mount_repo_dir)

            output += self.execute(['git', 'config', 'remote.origin.url', clone_url], cwd=mount_repo_dir)
            output += self.execute(['git', 'config', 'remote.origin.fetch', '+refs/heads/*:refs/remotes/origin/*'],
                                   cwd=mount_repo_dir)

            if not clone_all:
                output += self.execute(['git', 'fetch', 'origin', commit], cwd=mount_repo_dir)

            cmd = ['git', 'checkout', '-qf', commit]

            #if not branch:
            #    cmd += ['-b', 'infrabox']

            output += self.execute(cmd, cwd=mount_repo_dir)

            if submodules:
                output += self.execute(['git', 'submodule', 'init'], cwd=mount_repo_dir)
                output += self.execute(['git', 'submodule', 'update'], cwd=mount_repo_dir)

            return output
        except subprocess.CalledProcessError as e:
            return output + e.output + "\n" + str(e), 500
        except Exception as e:
            return traceback.format_exc(), 500


def main(): # pragma: no cover
    logger.info('Starting Server')
    http_server = WSGIServer(('0.0.0.0', 8080), app)
    http_server.serve_forever()

if __name__ == "__main__": # pragma: no cover
    try:
        main()
    except:
        print_stackdriver()
