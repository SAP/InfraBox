#!/usr/bin/env python
import argparse
import os
import re
import subprocess
import logging
import sys

from Crypto.PublicKey import RSA

logging.basicConfig(
    format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%d-%m-%Y:%H:%M:%S',
    level=logging.WARNING
)

logger = logging.getLogger('ib')

IMAGES = [
    {'name': 'gerrit-api'},
    {'name': 'gerrit-trigger'},
    {'name': 'gerrit-review'},
    {'name': 'github-trigger'},
    {'name': 'github-review'},
    {'name': 'job'},
    {'name': 'job-git'},
    {'name': 'scheduler-kubernetes'},
    {'name': 'scheduler-docker-compose'},
    {'name': 'docker-compose-ingress'},
    {'name': 'docker-compose-minio-init'},
    {'name': 'api'},
    {'name': 'dashboard-api'},
    {'name': 'build-dashboard-client'},
    {'name': 'static', 'depends_on': ['build-dashboard-client']},
    {'name': 'docker-auth'},
    {'name': 'docker-nginx'},
    {'name': 'db'},
    {'name': 'docker-gc'},
    {'name': 'postgres'},
]

def execute(command, cwd=None, env=None, ignore_error=False, ignore_output=False):
    if env is None:
        env = os.environ

    process = subprocess.Popen(command,
                               shell=False,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               cwd=cwd,
                               env=env,
                               universal_newlines=True)

    # Poll process for new output until finished
    while True:
        line = process.stdout.readline()
        if not line:
            break

        if ignore_output:
            continue

        print(line.rstrip())

    process.wait()

    if ignore_error:
        return

    exitCode = process.returncode
    if exitCode != 0:
        raise Exception(exitCode)

def _build_image(image, args):
    if image.get('executed', False):
        return

    for d in image.get('depends_on', []):
        for i in IMAGES:
            if i['name'] == d:
                _build_image(i, args)
                break

    image_name = '%s/infrabox/%s:%s' % (args.registry, image['name'], args.tag)
    job = 'ib/deploy/%s' % image['name']

    execute(['infrabox', 'run', job, '-t', image_name])

    image['executed'] = True

def images_build(args):
    for i in IMAGES:
        if not re.match(args.filter, i['name']):
            continue

        _build_image(i, args)


def images_push(args):
    for image in IMAGES:
        if not re.match(args.filter, image['name']):
            continue

        image_name = '%s/infrabox/%s:%s' % (args.registry, image['name'], args.tag)

        if args.type == 'registry':
            execute(['docker', 'push', image_name])
        elif args.type == 'gcr':
            execute(['gcloud', 'docker', '--', 'push', image_name])
        else:
            print 'invalid type'
            sys.exit(1)

def _setup_rsa_keys():
    private_key_path = '/tmp/ib/run/rsa/id_rsa'
    public_key_path = '/tmp/ib/run/rsa/id_rsa.pub'

    key = RSA.generate(2048)

    if not os.path.exists(private_key_path):
        logger.warn('Private key does not exist: %s', private_key_path)
        logger.warn('Recreating it')

        if not os.path.exists(os.path.dirname(private_key_path)):
            os.makedirs(os.path.dirname(private_key_path))

        with open(private_key_path, 'w+') as s:
            s.write(str(key.exportKey()))

    if not os.path.exists(public_key_path):
        logger.warn('Public key does not exist: %s', public_key_path)
        logger.warn('Recreating it')

        if not os.path.exists(os.path.dirname(public_key_path)):
            os.makedirs(os.path.dirname(public_key_path))

        with open(public_key_path, 'w+') as s:
            s.write(str(key.publickey().exportKey()))

def services_start(args):
    if args.service_name == 'storage':
        execute(['docker-compose', 'up'], cwd=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'infrabox', 'utils', 'storage'))
    elif args.service_name == 'api':
        p = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'src', 'api')
        run = os.path.join(p, 'run_with_dummy.sh')
        execute(['bash', run], cwd=p)
    elif args.service_name == 'dashboard_api':
        _setup_rsa_keys()
        p = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'src', 'dashboard_api')
        run = os.path.join(p, 'run_with_dummy.sh')
        execute(['bash', run], cwd=p)
    elif args.service_name == 'dashboard-client':
        p = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'src', 'dashboard-client')
        execute(['npm', 'run', 'dev'], cwd=p)
    else:
        print "Unknown service"
        sys.exit(1)

def services_rm(args):
    if args.service_name == 'storage':
        execute(['docker-compose', 'rm', '-f'], cwd=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'infrabox', 'utils', 'storage'))
    else:
        print "Unknown service"
        sys.exit(1)

def services_kill(args):
    if args.service_name == 'storage':
        execute(['docker-compose', 'kill'], cwd=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'infrabox', 'utils', 'storage'))
    else:
        print "Unknown service"
        sys.exit(1)

def changelog_create(args):
    # Build docker container
    container_name = 'infrabox_changelog_container'
    command = ['docker', 'build', '-t', container_name, 'src/utils/changelog_generator']
    execute(command, cwd=os.getcwd())

    command = ['docker', 'run', '-it', '-v', os.getcwd() + ':/infrabox_changelog', container_name]
    if args.token:
        command.append('--token')
        command.append(args.token)

    command.append('--no-verbose')
    repo_name = 'infrabox/infrabox'
    command.append(repo_name)
    execute(command, cwd=os.getcwd())


def main():
    parser = argparse.ArgumentParser(prog="ib")
    cmd_parser = parser.add_subparsers()

    # Images
    images = cmd_parser.add_parser('images')
    sub_images = images.add_subparsers()

    images_build_parser = sub_images.add_parser('build')
    images_build_parser.set_defaults(func=images_build)
    images_build_parser.add_argument("--registry", default='localhost:5000')
    images_build_parser.add_argument("--tag", default='latest')
    images_build_parser.add_argument("--filter", default='.*')

    images_push_parser = sub_images.add_parser('push')
    images_push_parser.set_defaults(func=images_push)
    images_push_parser.add_argument("--registry", default='localhost:5000')
    images_push_parser.add_argument("--tag", default='latest')
    images_push_parser.add_argument("--filter", default='.*')
    images_push_parser.add_argument("--type", default='registry')

    # Service
    services = cmd_parser.add_parser('services')
    sub_services = services.add_subparsers()

    services_start_parser = sub_services.add_parser('start')
    services_start_parser.set_defaults(func=services_start)
    services_start_parser.add_argument("service_name", nargs="?", type=str, help="Service name")

    services_rm_parser = sub_services.add_parser('rm')
    services_rm_parser.set_defaults(func=services_rm)
    services_rm_parser.add_argument("service_name", nargs="?", type=str, help="Service name")

    services_kill_parser = sub_services.add_parser('kill')
    services_kill_parser.set_defaults(func=services_kill)
    services_kill_parser.add_argument("service_name", nargs="?", type=str, help="Service name")

    # Github changelog
    changelog = cmd_parser.add_parser('changelog')
    sub_changelog = changelog.add_subparsers()

    create_changelog_parser = sub_changelog.add_parser('create')
    create_changelog_parser.set_defaults(func=changelog_create)
    create_changelog_parser.add_argument("--token", required=False)


    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
