import argparse
import os
import sys
import stat
import random
import string
import shutil
import base64
import logging
import yaml

logging.basicConfig(
    format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%d-%m-%Y:%H:%M:%S',
    level=logging.WARN
)

logger = logging.getLogger("install")


class Configuration(object):
    def __init__(self):
        self.config = {}

    def add(self, name, value):
        elements = name.split('.')

        c = self.config
        for e in elements[:-1]:
            if e not in c:
                c[e] = {}

            c = c[e]

        c[elements[-1]] = value

    def append(self, name, values):
        elements = name.split('.')

        c = self.config
        for e in elements[:-1]:
            if e not in c:
                c[e] = {}

            c = c[e]


        k = elements[-1]
        if k not in c:
            c[k] = []

        c[k] += values

    def dump(self, p):
        with open(p, 'w') as outfile:
            yaml.dump(self.config, outfile, default_flow_style=False)

    def load(self, p):
        with open(p) as infile:
            self.config = yaml.load(infile)

def copy_files(args, directory):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    chart_dir = os.path.join(dir_path, directory)
    shutil.copytree(chart_dir, args.o)

def option_not_supported(args, name):
    args = vars(args)
    m = name.replace("-", "_")
    if args.get(m, None):
        print "--%s not supported" % name
        sys.exit(1)

class Install(object):
    def __init__(self, args):
        self.args = args

    def required_option(self, name):
        args = vars(self.args)
        m = name.replace("-", "_")
        if not args.get(m, None):
            print "--%s not set" % name
            sys.exit(1)

    def check_file_exists(self, p):
        if not os.path.exists(p):
            print "%s does not exist" % p
            sys.exit(1)

    def create_secret(self, name, namespace, data):
        secrets_dir = os.path.join(self.args.o, 'templates', 'secrets')

        if not os.path.exists(secrets_dir):
            os.mkdir(secrets_dir)

        d = {}

        for k, v in data.iteritems():
            d[k] = base64.b64encode(v)

        s = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": name,
                "namespace": namespace
            },
            "type": "Opaque",
            "data": d
        }

        o = os.path.join(secrets_dir, namespace + '-' + name + '.yaml')
        with open(o, 'w') as outfile:
            yaml.dump(s, outfile, default_flow_style=False)

    def make_executable_file(self, path, content):
        with open(path, 'w') as outfile:
            outfile.write(content)

        st = os.stat(path)
        os.chmod(path, st.st_mode | stat.S_IEXEC)

class Kubernetes(Install):
    def __init__(self, args):
        super(Kubernetes, self).__init__(args)
        self.config = Configuration()

    def set(self, n, v):
        self.config.add(n, v)

    def setup_postgres(self):
        self.required_option('database')
        args = self.args

        if self.args.database == 'postgres':
            self.required_option('postgres-host')
            self.required_option('postgres-port')
            self.required_option('postgres-username')
            self.required_option('postgres-password')
            self.required_option('postgres-database')
            self.set('storage.postgres.enabled', True)
            self.set('storage.postgres.host', args.postgres_host)
            self.set('storage.postgres.port', args.postgres_port)
            self.set('storage.postgres.db', args.postgres_database)
            self.set('storage.cloudsql.enabled', False)

            secret = {
                "username": args.postgres_username,
                "password": args.postgres_password
            }

            self.create_secret("infrabox-postgres-db-credentials", "infrabox-worker", secret)
            self.create_secret("infrabox-postgres-db-credentials", "infrabox-system", secret)
        elif args.database == 'cloudsql':
            self.required_option('cloudsql-instance-connection-name')
            self.required_option('cloudsql-proxy-service-account-key-file')
            self.required_option('cloudsql-proxy-username')
            self.required_option('cloudsql-proxy-password')

            self.check_file_exists(args.cloudsql_proxy_service_account_key_file)

            self.set('storage.postgres.enabled', False)
            self.set('storage.postgres.host', "localhost")
            self.set('storage.postgres.port', 5432)
            self.set('storage.cloudsql.instance_connection_name', args.cloudsql_instance_connection_name)
            self.set('storage.cloudsql.enabled', True)

            secret = {
                "username": args.cloudsql_proxy_username,
                "password": args.cloudsql_proxy_password
            }

            self.create_secret("infrabox-cloudsql-db-credentials", "infrabox-worker", secret)
            self.create_secret("infrabox-cloudsql-db-credentials", "infrabox-system", secret)

            with open(args.cloudsql_proxy_service_account_key_file) as keyfile:
                secret = {
                    "credentials.json": keyfile.read()
                }

                self.create_secret("infrabox-cloudsql-instance-credentials", "infrabox-worker", secret)
                self.create_secret("infrabox-cloudsql-instance-credentials", "infrabox-system", secret)

        else:
            raise Exception('unknown database type')

    def setup_storage(self):
        self.required_option('storage')
        args = self.args

        if args.storage == 's3':
            self.required_option('s3-access-key')
            self.required_option('s3-secret-key')
            self.required_option('s3-region')
            self.required_option('s3-endpoint')
            self.required_option('s3-port')
            self.required_option('s3-container-output-bucket')
            self.required_option('s3-project-upload-bucket')
            self.required_option('s3-container-content-cache-bucket')
            self.required_option('s3-docker-registry-bucket')

            self.set('storage.gcs.enabled', False)
            self.set('storage.s3.enabled', True)
            self.set('storage.s3.region', args.s3_region)
            self.set('storage.s3.endpoint', args.s3_endpoint)
            self.set('storage.s3.container_output_bucket', args.s3_container_output_bucket)
            self.set('storage.s3.project_upload_bucket', args.s3_project_upload_bucket)
            self.set('storage.s3.container_content_cache_bucket', args.s3_container_content_cache_bucket)
            self.set('storage.s3.docker_registry_bucket', args.s3_docker_registry_bucket)
            self.set('storage.s3.port', args.s3_port)
            self.set('storage.s3.secure', args.s3_secure == 'true')

            secret = {
                "secretKey": args.s3_secret_key,
                "accessKey": args.s3_access_key
            }

            self.create_secret("infrabox-s3-credentials", "infrabox-worker", secret)
            self.create_secret("infrabox-s3-credentials", "infrabox-system", secret)

        elif args.storage == 'gcs':
            self.required_option('gcs-project-id')
            self.required_option('gcs-service-account-key-file')
            self.required_option('gcs-container-output-bucket')
            self.required_option('gcs-project-upload-bucket')
            self.required_option('gcs-container-content-cache-bucket')
            self.required_option('gcs-docker-registry-bucket')

            self.check_file_exists(args.gcs_service_account_key_file)

            self.set('storage.s3.enabled', False)
            self.set('storage.gcs.enabled', True)
            self.set('storage.gcs.project_id', args.gcs_project_id)
            self.set('storage.gcs.container_output_bucket', args.gcs_container_output_bucket)
            self.set('storage.gcs.project_upload_bucket', args.gcs_project_upload_bucket)
            self.set('storage.gcs.container_content_cache_bucket', args.gcs_container_content_cache_bucket)
            self.set('storage.gcs.docker_registry_bucket', args.gcs_docker_registry_bucket)

            with open(args.gcs_service_account_key_file) as keyfile:
                secret = {
                    "gcs_service_account.json": keyfile.read()
                }

                self.create_secret("infrabox-gcs", "infrabox-worker", secret)
                self.create_secret("infrabox-gcs", "infrabox-system", secret)
        else:
            raise Exception("unknown storage")

    def setup_docker_registry(self):
        self.required_option('docker-registry-admin-username')
        self.required_option('docker-registry-admin-password')
        self.required_option('docker-registry-url')

        secret = {
            "username": self.args.docker_registry_admin_username,
            "password": self.args.docker_registry_admin_password
        }

        self.create_secret("infrabox-docker-registry", "infrabox-system", secret)
        self.create_secret("infrabox-docker-registry", "infrabox-worker", secret)

        self.required_option('docker-registry')
        self.set('general.docker_registry', self.args.docker_registry)

        if self.args.use_k8s_nodeports:
            self.set('docker_registry.node_port', self.args.docker_registry_k8s_nodeport)

        self.set('docker_registry.url', self.args.docker_registry_url)

        if self.args.docker_registry_tls_enabled:
            self.required_option('docker-registry-tls-key-file')
            self.required_option('docker-registry-tls-crt-file')

            self.check_file_exists(self.args.docker_registry_tls_key_file)
            self.check_file_exists(self.args.docker_registry_crt_key_file)

            secret = {
                "server.key": open(self.args.docker_registry_tls_key_file).read(),
                "server.crt": open(self.args.docker_registry_tls_crt_file).read()
            }

            self.create_secret("infrabox-docker_registry-tls", "infrabox-system", secret)

    def setup_ldap(self):
        if not self.args.ldap_enabled:
            return

        self.required_option('ldap-dn')
        self.required_option('ldap-password')
        self.required_option('ldap-base')
        self.required_option('ldap-url')

        secret = {
            "dn": self.args.ldap_dn,
            "password": self.args.ldap_password
        }

        self.create_secret("infrabox-ldap", "infrabox-system", secret)

        self.set('account.ldap.enabled', True)
        self.set('account.ldap.base', self.args.ldap_base)
        self.set('account.ldap.url', self.args.ldap_url)
        self.set('account.signup.enabled', False)

    def setup_gerrit(self):
        if not self.args.github_enabled:
            return

        self.required_option('gerrit-hostname')
        self.required_option('gerrit-port')
        self.required_option('gerrit-username')
        self.required_option('gerrit-private-key')

        self.set('gerrit.enabled', True)
        self.set('gerrit.hostname', self.args.github_hostname)
        self.set('gerrit.username', self.args.github_username)

        self.check_file_exists(self.args.gerrit_private_key)

        secret = {
            "id_rsa": open(self.args.gerrit_private_key).read()
        }

        self.create_secret("infrabox-gerrit-ssh", "infrabox-system", secret)
        self.create_secret("infrabox-gerrit-ssh", "infrabox-worker", secret)

    def setup_github(self):
        if not self.args.github_enabled:
            return

        self.required_option('github-client-id')
        self.required_option('github-client-secret')
        self.required_option('github-api-url')
        self.required_option('github-login-url')
        self.required_option('github-login-enabled')

        self.set('github.enabled', True)
        self.set('github.login.enabled', self.args.github_login_enabled)
        self.set('github.login.url', self.args.github_login_url)
        self.set('github.api_url', self.args.github_api_url)

        secret = {
            "client_id": self.args.github_client_id,
            "client_secret": self.args.github_client_secret,
            "webhook_secret": ''.join([random.choice(string.lowercase) for _ in xrange(32)])
        }

        self.create_secret("infrabox-gerrit-ssh", "infrabox-system", secret)

    def setup_dashboard(self):
        self.required_option('dashboard-url')

        secret = {
            "secret": ''.join([random.choice(string.lowercase) for _ in xrange(32)])
        }

        self.create_secret("infrabox-dashboard", "infrabox-system", secret)

        if self.args.use_k8s_nodeports:
            self.set('dashboard.node_port', self.args.dashboard_k8s_nodeport)

        self.set('dashboard.url', self.args.dashboard_url)

        if self.args.dashboard_tls_enabled:
            self.required_option('dashboard-tls-key-file')
            self.required_option('dashboard-tls-crt-file')

            self.check_file_exists(self.args.dashboard_tls_key_file)
            self.check_file_exists(self.args.dashboard_crt_key_file)

            secret = {
                "server.key": open(self.args.dashboard_tls_key_file).read(),
                "server.crt": open(self.args.dashboard_tls_crt_file).read()
            }

            self.create_secret("infrabox-dashboard-tls", "infrabox-system", secret)


    def setup_api(self):
        self.required_option('api-url')

        if self.args.use_k8s_nodeports:
            self.set('api.node_port', self.args.api_k8s_nodeport)

        self.set('api.url', self.args.api_url)

        if self.args.api_tls_enabled:
            self.required_option('api-tls-key-file')
            self.required_option('api-tls-crt-file')

            self.check_file_exists(self.args.api_tls_key_file)
            self.check_file_exists(self.args.api_crt_key_file)

            secret = {
                "server.key": open(self.args.api_tls_key_file).read(),
                "server.crt": open(self.args.api_tls_crt_file).read()
            }

            self.create_secret("infrabox-api-tls", "infrabox-system", secret)


    def setup_docs(self):
        self.required_option('docs-url')

        if self.args.use_k8s_nodeports:
            self.set('docs.node_port', self.args.docs_k8s_nodeport)

        self.set('docs.url', self.args.docs_url)

        if self.args.docs_tls_enabled:
            self.required_option('docs-tls-key-file')
            self.required_option('docs-tls-crt-file')

            self.check_file_exists(self.args.docs_tls_key_file)
            self.check_file_exists(self.args.docs_crt_key_file)

            secret = {
                "server.key": open(self.args.docs_tls_key_file).read(),
                "server.crt": open(self.args.docs_tls_crt_file).read()
            }

            self.create_secret("infrabox-docs-tls", "infrabox-system", secret)


    def main(self):
        # Copy helm chart
        copy_files(self.args, 'infrabox')

        self.setup_postgres()
        self.setup_storage()
        self.setup_docker_registry()
        self.setup_gerrit()
        self.setup_github()
        self.setup_dashboard()
        self.setup_api()
        self.setup_docs()
        self.setup_ldap()

        self.config.dump(os.path.join(self.args.o, 'values-generated.yaml'))

        install = '''
#!/bin/bash -e

command -v helm >/dev/null 2>&1 || { echo >&2 "I require helm but it's not installed. Aborting."; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo >&2 "I require kubectl but it's not installed. Aborting."; exit 1; }

kubectl create namespace infrabox-system
kubectl create namespace infrabox-worker

helm install -n infrabox -f values-generated.yaml .
'''

        install_path = os.path.join(self.args.o, 'install.sh')
        self.make_executable_file(install_path, install)

        update = '''
#!/bin/bash -e

command -v helm >/dev/null 2>&1 || { echo >&2 "I require helm but it's not installed. Aborting."; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo >&2 "I require kubectl but it's not installed. Aborting."; exit 1; }

helm upgrade infrabox -f values-generated.yaml .
'''

        update_path = os.path.join(self.args.o, 'update.sh')
        self.make_executable_file(update_path, update)

        pf = '''
#!/bin/bash -e
command -v kubectl >/dev/null 2>&1 || { echo >&2 "I require kubectl but it's not installed. Aborting."; exit 1; }

#!/bin/bash -e
component=$1
port=$2
echo "Looking for a pod for: $component"

pod=$(kubectl get pods -n infrabox-system | grep $component | awk '{ print $1 }')

echo "Found pod: $pod"
echo "Starting port-forwarding: $port"

kubectl port-forward -n infrabox-system $pod $port
'''

        pf_path = os.path.join(self.args.o, 'port-forward.sh')
        self.make_executable_file(pf_path, pf)


class DockerCompose(Install):
    def __init__(self, args):
        super(DockerCompose, self).__init__(args)
        self.config = Configuration()

    def setup_docker_registry(self):
        self.required_option('docker-registry')
        self.config.add('services.api.image', '%s/infrabox/api' % self.args.docker_registry)
        self.config.add('services.dashboard.image', '%s/infrabox/dashboard' % self.args.docker_registry)
        self.config.add('services.db.image', '%s/infrabox/db' % self.args.docker_registry)
        self.config.add('services.scheduler.image', '%s/infrabox/scheduler/docker-compose' % self.args.docker_registry)
        self.config.append('services.scheduler.environment',
                           ['INFRABOX_DOCKER_REGISTRY=%s' % self.args.docker_registry])

    def setup_ldap(self):
        if self.args.ldap_enabled:
            self.required_option('ldap-dn')
            self.required_option('ldap-password')
            self.required_option('ldap-base')
            self.required_option('ldap-url')

            env = [
                "INFRABOX_ACCOUNT_LDAP_ENABLED=true",
                "INFRABOX_ACCOUNT_LDAP_BASE=%s" % self.args.ldap_base,
                "INFRABOX_ACCOUNT_LDAP_URL=%s" % self.args.ldap_url,
                "INFRABOX_ACCOUNT_LDAP_DN=%s" % self.args.ldap_dn,
                "INFRABOX_ACCOUNT_LDAP_PASSWORD=%s" % self.args.ldap_password,
                "INFRABOX_ACCOUNT_SIGNUP_ENABLED=false"
            ]

        else:
            env = [
                "INFRABOX_ACCOUNT_SIGNUP_ENABLED=true"
            ]

        self.config.append('services.dashboard.environment', env)


    def setup_database(self):
        if self.args.database == 'postgres':
            self.required_option('postgres-host')
            self.required_option('postgres-port')
            self.required_option('postgres-username')
            self.required_option('postgres-password')
            self.required_option('postgres-database')

            env = [
                'INFRABOX_DATABASE_USER=%s' % self.args.postgres_username,
                'INFRABOX_DATABASE_PASSWORD=%s' % self.args.postgres_password,
                'INFRABOX_DATABASE_HOST=%s' % self.args.postgres_host,
                'INFRABOX_DATABASE_PORT=%s' % self.args.postgres_port,
                'INFRABOX_DATABASE_DB=%s' % self.args.postgres_database
            ]

            del self.config.config['services']['postgres']
        else:
            if self.args.database:
                logger.warn("--database=%s not supported", self.args.database)

            env = [
                'INFRABOX_DATABASE_USER=postgres',
                'INFRABOX_DATABASE_PASSWORD=postgres',
                'INFRABOX_DATABASE_HOST=localhost',
                'INFRABOX_DATABASE_PORT=5432',
                'INFRABOX_DATABASE_DB=postgres'
            ]


        self.config.append('services.db.environment', env)
        self.config.append('services.dashboard.environment', env)
        self.config.append('services.api.environment', env)
        self.config.append('services.scheduler.environment', env)

    def setup_init_file(self):
        init = '''
#!/bin/bash -e

mc config host add compose http://localhost:9000 AKIAIOSFODNN7EXAMPLE wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY S3v4
mc mb compose/infrabox-container-content-cache
mc mb compose/infrabox-project-upload
mc mb compose/infrabox-container-output
mc mb compose/infrabox-docker-registry
'''

        init_path = os.path.join(self.args.o, 'init.sh')
        self.make_executable_file(init_path, init)


    def main(self):
        copy_files(self.args, 'compose')

        compose_path = os.path.join(self.args.o, 'docker-compose.yml')
        self.config.load(compose_path)
        self.setup_database()
        self.setup_docker_registry()
        self.setup_init_file()
        self.setup_ldap()
        self.config.dump(compose_path)


def main():
    parser = argparse.ArgumentParser(description='Install InfraBox')
    parser.add_argument('-o',
                        required=True,
                        help="Output directory in which the configuration should be stored")


    # Platform
    parser.add_argument('--platform',
                        choices=['docker-compose', 'kubernetes'],
                        required=True)

    # Docker configuration
    parser.add_argument('--docker-registry',
                        required=True)
    parser.add_argument('--docker-registry-admin-username')
    parser.add_argument('--docker-registry-admin-password')
    parser.add_argument('--docker-registry-k8s-nodeport', type=int, default=30202)
    parser.add_argument('--docker-registry-url')
    parser.add_argument('--docker-registry-tls-enabled', action='store_true', default=False)
    parser.add_argument('--docker-registry-tls-key-file')
    parser.add_argument('--docker-registry-tls-crt-file')

    # Database configuration
    parser.add_argument('--database',
                        choices=['postgres', 'cloudsql'],
                        help='Which kind of postgres database you want to use')

    parser.add_argument('--postgres-host')
    parser.add_argument('--postgres-port', default=5432, type=int)
    parser.add_argument('--postgres-username')
    parser.add_argument('--postgres-password')
    parser.add_argument('--postgres-database')

    parser.add_argument('--cloudsql-instance-connection-name')
    parser.add_argument('--cloudsql-proxy-service-account-key-file')
    parser.add_argument('--cloudsql-proxy-username')
    parser.add_argument('--cloudsql-proxy-password')

    # Storage configuration
    parser.add_argument('--storage',
                        choices=['s3', 'gcs'],
                        help='Which kind of storage you want to use')

    parser.add_argument('--s3-access-key')
    parser.add_argument('--s3-secret-key')
    parser.add_argument('--s3-region')
    parser.add_argument('--s3-endpoint')
    parser.add_argument('--s3-port', default=443, type=int)
    parser.add_argument('--s3-container-output-bucket', default='infrabox-container-output-bucket')
    parser.add_argument('--s3-project-upload-bucket', default='infrabox-project-upload-bucket')
    parser.add_argument('--s3-container-content-cache-bucket', default='infrabox-container-cache-bucket')
    parser.add_argument('--s3-docker-registry-bucket', default='infrabox-docker-registry-bucket')
    parser.add_argument('--s3-secure', default='true')

    parser.add_argument('--gcs-project-id')
    parser.add_argument('--gcs-service-account-key-file')
    parser.add_argument('--gcs-container-output-bucket', default='infrabox-container-output-bucket')
    parser.add_argument('--gcs-project-upload-bucket', default='infrabox-project-upload-bucket')
    parser.add_argument('--gcs-container-content-cache-bucket', default='infrabox-container-cache-bucket')
    parser.add_argument('--gcs-docker-registry-bucket', default='infrabox-docker-registry-bucket')

    # Nodeport
    parser.add_argument('--use-k8s-nodeports', action='store_true', default=False)

    # Dashboard
    parser.add_argument('--dashboard-url')
    parser.add_argument('--dashboard-k8s-nodeport', type=int, default=30201)
    parser.add_argument('--dashboard-tls-enabled', action='store_true', default=False)
    parser.add_argument('--dashboard-tls-key-file')
    parser.add_argument('--dashboard-tls-crt-file')

    # API
    parser.add_argument('--api-url')
    parser.add_argument('--api-k8s-nodeport', type=int, default=30200)
    parser.add_argument('--api-tls-enabled', action='store_true', default=False)
    parser.add_argument('--api-tls-key-file')
    parser.add_argument('--api-tls-crt-file')

    # Docs
    parser.add_argument('--docs-url')
    parser.add_argument('--docs-k8s-nodeport', type=int, default=30203)
    parser.add_argument('--docs-tls-enabled', action='store_true', default=False)
    parser.add_argument('--docs-tls-key-file')
    parser.add_argument('--docs-tls-crt-file')

    # LDAP
    parser.add_argument('--ldap-enabled', action='store_true', default=False)
    parser.add_argument('--ldap-dn')
    parser.add_argument('--ldap-password')
    parser.add_argument('--ldap-base')
    parser.add_argument('--ldap-url')

    # Gerrit
    parser.add_argument('--gerrit-enabled', action='store_true', default=False)
    parser.add_argument('--gerrit-hostname')
    parser.add_argument('--gerrit-port')
    parser.add_argument('--gerrit-username')
    parser.add_argument('--gerrit-private-key')

    # Parse options
    args = parser.parse_args()
    if os.path.exists(args.o):
        print "%s does already exist" % args.o
        sys.exit(1)

    if args.platform == 'docker-compose':
        d = DockerCompose(args)
        d.main()
    elif args.platform == 'kubernetes':
        k = Kubernetes(args)
        k.main()
    else:
        raise Exception("unknown platform")

if __name__ == '__main__':
    main()
