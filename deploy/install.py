import argparse
import os
import json
import sys
import stat
import shutil
import base64
import logging
import yaml

from Crypto.PublicKey import RSA

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
        if k not in c or not c[k]:
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
    target_path = os.path.join(args.o, directory)
    shutil.copytree(chart_dir, target_path)

def option_not_supported(args, name):
    args = vars(args)
    m = name.replace("-", "_")
    if args.get(m, None):
        print "--%s not supported" % name
        sys.exit(1)

class Install(object):
    def __init__(self, args):
        self.args = args

    def is_master(self):
        return self.args.cluster_name == "master"

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
        secrets_dir = os.path.join(self.args.o, 'infrabox', 'templates', 'secrets')

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
        if not self.is_master():
            self.set('storage.migration.enabled', False)

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

            self.create_secret("infrabox-postgres", self.args.general_system_namespace, secret)
        elif args.database == 'cloudsql':
            self.required_option('cloudsql-instance-connection-name')
            self.required_option('cloudsql-proxy-service-account-key-file')
            self.required_option('cloudsql-proxy-username')
            self.required_option('cloudsql-proxy-password')
            self.required_option('postgres-database')

            self.check_file_exists(args.cloudsql_proxy_service_account_key_file)

            self.set('storage.postgres.enabled', False)
            self.set('storage.postgres.host', "localhost")
            self.set('storage.postgres.port', 5432)
            self.set('storage.postgres.db', args.postgres_database)
            self.set('storage.cloudsql.instance_connection_name', args.cloudsql_instance_connection_name)
            self.set('storage.cloudsql.enabled', True)

            secret = {
                "username": args.cloudsql_proxy_username,
                "password": args.cloudsql_proxy_password
            }

            self.create_secret("infrabox-postgres", self.args.general_system_namespace, secret)

            with open(args.cloudsql_proxy_service_account_key_file) as keyfile:
                secret = {
                    "credentials.json": keyfile.read()
                }

                self.create_secret("infrabox-cloudsql-instance-credentials", self.args.general_system_namespace, secret)

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
            self.required_option('s3-bucket')

            self.set('storage.gcs.enabled', False)
            self.set('storage.azure.enabled', False)
            self.set('storage.s3.enabled', True)
            self.set('storage.s3.region', args.s3_region)
            self.set('storage.s3.endpoint', args.s3_endpoint)
            self.set('storage.s3.bucket', args.s3_bucket)
            self.set('storage.s3.port', args.s3_port)
            self.set('storage.s3.secure', args.s3_secure == 'true')

            secret = {
                "secretKey": args.s3_secret_key,
                "accessKey": args.s3_access_key
            }

            self.create_secret("infrabox-s3-credentials", self.args.general_system_namespace, secret)
        elif args.storage == 'gcs':
            self.required_option('gcs-service-account-key-file')
            self.required_option('gcs-bucket')

            self.check_file_exists(args.gcs_service_account_key_file)

            self.set('storage.s3.enabled', False)
            self.set('storage.azure.enabled', False)
            self.set('storage.gcs.enabled', True)
            self.set('storage.gcs.bucket', args.gcs_bucket)

            with open(args.gcs_service_account_key_file) as keyfile:
                secret = {
                    "gcs_service_account.json": keyfile.read()
                }

                self.create_secret("infrabox-gcs", self.args.general_system_namespace, secret)
        elif args.storage == 'azure':
            self.required_option('azure-account-name')
            self.required_option('azure-account-key')

            self.set('storage.gcs.enabled', False)
            self.set('storage.s3.enabled', False)
            self.set('storage.azure.enabled', True)

            secret = {
                "account-name": args.azure_account_name,
                "account-key": args.azure_account_key
            }
            self.create_secret("infrabox-azure-credentials", self.args.general_system_namespace, secret)
        else:
            raise Exception("unknown storage")

    def setup_admin_password(self):
        self.required_option('admin-password')
        self.required_option('admin-email')

        secret = {
            "email": self.args.admin_email,
            "password": self.args.admin_password
        }

        self.create_secret("infrabox-admin", self.args.general_system_namespace, secret)

    def setup_docker_registry(self):
        self.set('docker_registry.nginx_tag', self.args.version)
        self.set('docker_registry.auth_tag', self.args.version)

        self.required_option('docker-registry')
        self.set('general.docker_registry', self.args.docker_registry)
        self.set('docker_registry.url', self.args.root_url)

    def setup_account(self):
        self.set('account.signup.enabled', self.args.account_signup_enabled)

    def setup_local_cache(self):
        self.set('local_cache.enabled', self.args.local_cache_enabled)

        if self.args.local_cache_enabled:
            self.required_option('local-cache-host-path')
            self.set('local_cache.host_path', self.args.local_cache_host_path)

    def setup_ldap(self):
        if not self.is_master():
            return

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

        self.create_secret("infrabox-ldap", self.args.general_system_namespace, secret)

        self.set('account.ldap.enabled', True)
        self.set('account.ldap.base', self.args.ldap_base)
        self.set('account.ldap.url', self.args.ldap_url)
        self.set('account.signup.enabled', False)

    def setup_gerrit(self):
        if not self.is_master():
            return

        if not self.args.gerrit_enabled:
            return

        self.required_option('gerrit-hostname')
        self.required_option('gerrit-port')
        self.required_option('gerrit-username')
        self.required_option('gerrit-private-key')

        self.set('gerrit.enabled', True)
        self.set('gerrit.hostname', self.args.gerrit_hostname)
        self.set('gerrit.username', self.args.gerrit_username)
        self.set('gerrit.review.enabled', self.args.gerrit_review_enabled)
        self.set('gerrit.review.tag', self.args.version)
        self.set('gerrit.trigger.tag', self.args.version)
        self.set('gerrit.api.tag', self.args.version)

        self.check_file_exists(self.args.gerrit_private_key)

        secret = {
            "id_rsa": open(self.args.gerrit_private_key).read()
        }

        self.create_secret("infrabox-gerrit-ssh", self.args.general_system_namespace, secret)
        self.create_secret("infrabox-gerrit-ssh", self.args.general_worker_namespace, secret)

    def setup_github(self):
        if not self.is_master():
            return

        if not self.args.github_enabled:
            return

        self.required_option('github-client-id')
        self.required_option('github-client-secret')
        self.required_option('github-webhook-secret')
        self.required_option('github-api-url')
        self.required_option('github-login-url')

        self.set('github.enabled', True)
        self.set('github.login.enabled', self.args.github_login_enabled)
        self.set('github.login.url', self.args.github_login_url)
        self.set('github.api_url', self.args.github_api_url)
        self.set('github.trigger.tag', self.args.version)
        self.set('github.api.tag', self.args.version)
        self.set('github.review.tag', self.args.version)
        self.set('github.login.allowed_organizations', self.args.github_login_allowed_organizations)

        secret = {
            "client_id": self.args.github_client_id,
            "client_secret": self.args.github_client_secret,
            "webhook_secret": self.args.github_webhook_secret
        }

        self.create_secret("infrabox-github", self.args.general_system_namespace, secret)

    def setup_dashboard(self):
        if not self.is_master():
            self.set('dashboard.enabled', False)
        else:
            self.set('dashboard.api.tag', self.args.version)
            self.set('dashboard.url', self.args.root_url)

    def setup_api(self):
        self.set('api.url', self.args.root_url + '/api/cli')
        self.set('api.tag', self.args.version)

    def setup_static(self):
        if not self.is_master():
            self.set('static.enabled', False)
        else:
            self.set('static.tag', self.args.version)

    def setup_general(self):
        self.required_option('general-rsa-private-key')
        self.required_option('general-rsa-public-key')

        self.set('general.dont_check_certificates', self.args.general_dont_check_certificates)
        self.set('general.worker_namespace', self.args.general_worker_namespace)
        self.set('general.system_namespace', self.args.general_system_namespace)
        self.set('general.rbac.enabled', not self.args.general_rbac_disabled)
        self.set('general.report_issue_url', self.args.general_report_issue_url)
        self.set('root_url', self.args.root_url)

        self.check_file_exists(self.args.general_rsa_private_key)
        self.check_file_exists(self.args.general_rsa_public_key)

        secret = {
            "id_rsa": open(self.args.general_rsa_private_key).read(),
            "id_rsa.pub": open(self.args.general_rsa_public_key).read()
        }

        self.create_secret("infrabox-rsa", self.args.general_system_namespace, secret)

    def setup_job(self):
        self.set('job.mount_docker_socket', self.args.job_mount_docker_socket)
        self.set('job.use_host_docker_daemon', self.args.job_use_host_docker_daemon)
        self.set('job.security_context.capabilities.enabled',
                 self.args.job_security_context_capabilities_enabled)

        self.set('job.api.url', self.args.root_url + '/api/job')
        self.set('job.api.tag', self.args.version)

    def setup_db(self):
        self.set('db.tag', self.args.version)

    def setup_scheduler(self):
        self.set('scheduler.tag', self.args.version)
        self.set('scheduler.enabled', not self.args.scheduler_disabled)
        self.set('controller.tag', self.args.version)

    def setup_cluster(self):
        self.set('cluster.name', self.args.cluster_name)
        self.set('cluster.labels', self.args.cluster_labels)

    def setup_ingress(self):
        host = self.args.root_url.replace('http://', '')
        host = host.replace('https://', '')

        if not self.args.ingress_tls_host:
            self.args.ingress_tls_host = host.split(':')[0]

        self.set('ingress.tls.force_redirect', not self.args.ingress_tls_dont_force_redirect)
        self.set('ingress.tls.enabled', not self.args.ingress_tls_disabled)
        self.set('ingress.tls.host', self.args.ingress_tls_host)

    def main(self):
        self.required_option('root-url')

        while True:
            if self.args.root_url.endswith('/'):
                self.args.root_url = self.args.root_url[:-1]
            else:
                break

        # Copy helm chart
        copy_files(self.args, 'infrabox')

        # Load values
        values_path = os.path.join(self.args.o, 'infrabox', 'values.yaml')
        self.config.load(values_path)

        self.setup_general()
        self.setup_admin_password()
        self.setup_storage()
        self.setup_postgres()
        self.setup_docker_registry()
        self.setup_account()
        self.setup_job()
        self.setup_db()
        self.setup_scheduler()
        self.setup_cluster()
        self.setup_gerrit()
        self.setup_github()
        self.setup_dashboard()
        self.setup_api()
        self.setup_static()
        self.setup_ldap()
        self.setup_local_cache()
        self.setup_ingress()

        daemon_config = {
            'disable-legacy-registry': True
        }

        if self.args.general_dont_check_certificates:
            registry_name = self.args.root_url.replace('http://', '')
            registry_name = registry_name.replace('https://', '')
            daemon_config['insecure-registries'] = [registry_name]
            daemon_config_path = os.path.join(self.args.o, 'infrabox', 'config', 'docker', 'daemon.json')
            json.dump(daemon_config, open(daemon_config_path, 'w'))

        self.config.dump(values_path)

def main():
    parser = argparse.ArgumentParser(description='Install InfraBox')
    parser.add_argument('-o',
                        required=True,
                        help="Output directory in which the configuration should be stored")


    # Platform
    parser.add_argument('--version', default='latest')
    parser.add_argument('--root-url')
    parser.add_argument('--docker-registry', default='quay.io/infrabox')

    # Cluster
    parser.add_argument('--cluster-name', default='master')
    parser.add_argument('--cluster-labels')

    # Admin config
    parser.add_argument('--admin-email')
    parser.add_argument('--admin-password')

    # General
    parser.add_argument('--general-dont-check-certificates', action='store_true', default=False)
    parser.add_argument('--general-worker-namespace', default='infrabox-worker')
    parser.add_argument('--general-system-namespace', default='infrabox-system')
    parser.add_argument('--general-rsa-public-key')
    parser.add_argument('--general-rsa-private-key')
    parser.add_argument('--general-rbac-disabled', action='store_true', default=False)
    parser.add_argument('--general-report-issue-url', default='https://github.com/SAP/infrabox/issues')

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
                        choices=['s3', 'gcs', 'azure'],
                        help='Which kind of storage you want to use')

    parser.add_argument('--s3-access-key')
    parser.add_argument('--s3-secret-key')
    parser.add_argument('--s3-region')
    parser.add_argument('--s3-endpoint')
    parser.add_argument('--s3-port', default=443, type=int)
    parser.add_argument('--s3-bucket', default='infrabox')
    parser.add_argument('--s3-secure', default='true')

    parser.add_argument('--gcs-service-account-key-file')
    parser.add_argument('--gcs-bucket')

    parser.add_argument('--azure-account-name')
    parser.add_argument('--azure-account-key')

    # Scheduler
    parser.add_argument('--scheduler-disabled', action='store_true', default=False)

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
    parser.add_argument('--gerrit-review-enabled', action='store_true', default=False)

    # Github
    parser.add_argument('--github-enabled', action='store_true', default=False)
    parser.add_argument('--github-client-secret')
    parser.add_argument('--github-client-id')
    parser.add_argument('--github-webhook-secret')
    parser.add_argument('--github-api-url', default='https://api.github.com')
    parser.add_argument('--github-login-enabled', action='store_true', default=False)
    parser.add_argument('--github-login-url', default='https://github.com/login')
    parser.add_argument('--github-login-allowed-organizations', default="")

    # TLS
    parser.add_argument('--ingress-tls-disabled', action='store_true', default=False)
    parser.add_argument('--ingress-tls-host')
    parser.add_argument('--ingress-tls-dont-force-redirect', action='store_true', default=False)

    # Account
    parser.add_argument('--account-signup-enabled', action='store_true', default=False)

    # Local Cache
    parser.add_argument('--local-cache-enabled', action='store_true', default=False)
    parser.add_argument('--local-cache-host-path')

    # Job
    parser.add_argument('--job-mount-docker-socket', action='store_true', default=False)
    parser.add_argument('--job-use-host-docker-daemon', action='store_true', default=False)
    parser.add_argument('--job-security-context-capabilities-enabled', action='store_true', default=False)

    # Parse options
    args = parser.parse_args()
    if os.path.exists(args.o):
        print "%s does already exist" % args.o
        sys.exit(1)

    k = Kubernetes(args)
    k.main()

if __name__ == '__main__':
    main()
