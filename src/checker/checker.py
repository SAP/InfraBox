import argparse
import os
import time
import urllib3
import random
import string
import uuid
import requests
import psycopg2
import psycopg2.extensions

from pyinfraboxutils import get_logger, get_env
from pyinfraboxutils.storage import storage
from pyinfraboxutils.db import connect_db
from pyinfraboxutils.slack import SlackHook
from prometheus_client import Counter, Summary, start_http_server

class Checker(object):

    INFRABOX_API_DURATION = Summary(
        'infrabox_api_duration_seconds', 
        'Time spent processing request to InfraBox API')

    STORAGE_UPLOAD_DURATION = Summary(
        'storage_upload_duration_seconds', 
        'Time spent uploading file to storage')

    STORAGE_DOWNLOAD_DURATION = Summary(
        'storage_download_duration_seconds', 
        'Time spent downloading file to storage')

    DATABASE_SELECT1_DURATION = Summary(
        'database_select1_duration_seconds', 
        'Time spent executing "SELECT 1" into database')

    def __init__(self, conn, args):
        self.conn = conn
        self.args = args
        self.ha_enabled = get_env("INFRABOX_HA_ENABLED")
        self.monitoring_enabled = get_env("INFRABOX_MONITORING_ENABLED")
        self.namespace = get_env("INFRABOX_GENERAL_SYSTEM_NAMESPACE")
        self.check_interval = int(get_env('INFRABOX_HA_CHECK_INTERVAL'))
        self.active_timeout = get_env('INFRABOX_HA_ACTIVE_TIMEOUT')
        self.cluster_name = get_env('INFRABOX_CLUSTER_NAME')
        self.logger = get_logger("checker")
        self.root_url = get_env("INFRABOX_ROOT_URL")
        self.is_cluster_healthy = True
        self.retry_times = 0
        self.max_retry_times = 3
        self.infrabox_api_call_errors = Counter(
            'infrabox_api_errors_total', 
            'Errors in requests to InfraBox API')
        self.storage_checker_errors = Counter(
            'storage_checker_errors_total', 
            'Errors uploding/downloading files to/from storage')
        self.infrabox_dashboard_access_errors = Counter(
            'infrabox_dashboard_access_errors_total', 
            'Errors acessing dashboard')
        self.slack = CheckerSlackHook.get_from_env(self.logger)

    def _check_dashboard(self):
        try:
            r = requests.head(self.root_url, verify=False, timeout=5)
            self.logger.debug("Dashboard checking - HTTP Status code: %d" % r.status_code)
            if r.status_code != 200:
                self.infrabox_dashboard_access_errors.inc()
                return False
            return True
        except Exception as e:
            self.logger.exception('Got exception on check dashboard')
            self.infrabox_dashboard_access_errors.inc()
            return False
    
    def _check_api(self):
        try:
            r = self._request_api_with_metrics()
            self.logger.debug("Api checking - HTTP Status code: %d" % r.status_code)
            if r.status_code != 200:
                self.infrabox_api_call_errors.inc()
                return False
            return True
        except Exception as e:
            self.logger.exception('Got exception on check api')
            self.infrabox_api_call_errors.inc()
            return False

    @INFRABOX_API_DURATION.time()
    def _request_api_with_metrics(self):
        return requests.head(self.root_url + '/api/ping', verify=False, timeout=5)

    def _check_pods(self):
        try:
            h = {'Authorization': 'Bearer %s' % self.args.token}
            r = requests.get(
                self.args.api_server + '/api/v1/namespaces/%s/pods' % self.namespace,
                headers=h, timeout=10, verify=False)
            if r.status_code != 200:
                self.logger.debug('Pods checking - HTTP Status code: %d' % r.status_code)
                return False
            pods = r.json()['items']
            for pod in pods:
                if pod['status']['phase'] not in ['Running', 'Succeeded']:
                    msg = 'Pods checking - pod %s is in %s status' % \
                        (pod['metadata']['name'], pod['status']['phase'])
                    self.logger.debug(msg)
                    self.slack.warning(self.cluster_name, msg)
            return True
        except Exception as e:
            self.logger.exception('Got exception on check pods')
            return False

    def _create_random_file(self, file_name):
        contents = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(15))
        file_path = "/tmp/" + file_name
        with open(file_path, 'w') as f:
            f.write(contents)
        return file_path

    def _check_storage(self):
        file_name = "checker_test_"+ str(uuid.uuid4())
        file_path = self._create_random_file("checker_test_"+ str(uuid.uuid4()))
        download_path = ""
        try:
            with open(file_path, 'rb') as f:
                self._storage_upload_with_metrics(f, file_name)
            self.logger.debug("Storage checking - Upload file %s" % file_path)
            download_path = self._storage_download_with_metrics(file_name)
            self.logger.debug("Storage checking - Download file %s" %  download_path)
            return True
        except Exception as e:
            self.logger.exception('Got exception on check storage')
            self.storage_checker_errors.inc()
            return False
        finally:
            for f in [file_path, download_path]:
                if f is not None and os.path.exists(f):
                    os.remove(f)
            storage.delete_cache(file_name)

    @STORAGE_UPLOAD_DURATION.time()
    def _storage_upload_with_metrics(self, f, file_name):
        storage.upload_cache(f, file_name)

    @STORAGE_DOWNLOAD_DURATION.time()
    def _storage_download_with_metrics(self, file_name):
        storage.download_cache(file_name)

    @DATABASE_SELECT1_DURATION.time()
    def _check_database(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchall()
            cursor.close()
            return True
        except Exception as e:
             self.logger.exception('Exception checking database.')
             return False

    def _check_infrabox_status(self):
        return (self._check_pods()
            & self._check_dashboard()
            & self._check_api()
            & self._check_storage()
            & self._check_database())

    def _update_cluster_status(self, is_checking_healthy):
        
        if self.is_cluster_healthy != is_checking_healthy:
            self.is_cluster_healthy = is_checking_healthy
            self.retry_times = 0
        self.retry_times += 1

        if self.retry_times >= self.max_retry_times:
            self.retry_times = 0
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE cluster c SET active=%s
                FROM cluster prev
                WHERE c.name=%s AND prev.name=c.name
                RETURNING c.active active, prev.active prev_active
            """, [self.is_cluster_healthy, self.cluster_name])
            state_update = cursor.fetchall()
            if state_update and self.slack:
                if state_update[0][0] != state_update[0][1]:
                    self.logger.info("State change of cluster %s detected. Posting to slack [%s -> %s]",
                                     self.cluster_name, state_update[0][1], state_update[0][0])
                    if state_update[0][0]:
                        self.slack.notify_up(self.cluster_name, "self-check")
                    else:
                        self.slack.notify_down(self.cluster_name, "self-check")
            if self.is_cluster_healthy:
                cursor.execute("""
                    UPDATE cluster SET last_active=NOW()
                    WHERE name=%s
                """,[self.cluster_name])
            cursor.close()
            self.logger.info(
                "Set cluster %s active to %s. Reason: self check" % \
                (self.cluster_name, self.is_cluster_healthy))

    def _disable_clusters_with_outdated_active_time(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE cluster SET active=FALSE
            WHERE enabled=TRUE
                AND active=TRUE
                AND last_update < (NOW() - %s * INTERVAL '1' SECOND)
            RETURNING name, active
        """, [self.active_timeout])
        clusters = cursor.fetchall()
        cursor.close()
        for c in clusters:
            self.logger.info("Set cluster %s to inactive. "
                             "Reason: last update time is too old" % c[0])
            if self.slack:
                self.slack.notify_down(c[0], "inactivity")

    def run(self):
        self.logger.info("Starting InfraBox Checker")
        while True:
            is_checking_healthy = self._check_infrabox_status()
            if self.ha_enabled:
                self._update_cluster_status(is_checking_healthy)
                self._disable_clusters_with_outdated_active_time()
            time.sleep(self.check_interval)


class CheckerSlackHook(SlackHook):
    def __init__(self, hook_url, logger):
        super(CheckerSlackHook, self).__init__(hook_url)
        self.logger = logger

    def notify_up(self, cluster_name, reason):
        message = ":arrow_up_green: InfraBox cluster *{}* was activated by checker! [{}]".format(cluster_name, reason)
        return self._send_wrap_exception(message)

    def notify_down(self, cluster_name, reason):
        message = ":arrow_down_red: InfraBox cluster *{}* was deactivated by checker! [{}]".format(cluster_name, reason)
        return self._send_wrap_exception(message)

    def warning(self, cluster_name, msg):
        message = "WARNING! [{}] {}".format(cluster_name, msg)
        return self._send_wrap_exception(message)

    def _send_wrap_exception(self, message):
        try:
            self.send_status(message)
        except Exception as e:
            self.logger.exception("Error posting update to slack hook.")
            return False
        return True

    @classmethod
    def get_from_env(cls, logger):
        try:
            return cls(get_env("INFRABOX_CHECKER_SLACK_HOOK_URL"), logger)
        except:
            return None


def main():
    parser = argparse.ArgumentParser(prog="checker.py")
    args = parser.parse_args()

    # Validate if env vars are setted 
    get_env('INFRABOX_VERSION')
    get_env('INFRABOX_CLUSTER_NAME')
    get_env('INFRABOX_DATABASE_DB')
    get_env('INFRABOX_DATABASE_USER')
    get_env('INFRABOX_DATABASE_PASSWORD')
    get_env('INFRABOX_DATABASE_HOST')
    get_env('INFRABOX_DATABASE_PORT')
    get_env('INFRABOX_ROOT_URL')
    get_env('INFRABOX_HA_CHECK_INTERVAL')
    get_env('INFRABOX_HA_ACTIVE_TIMEOUT')

    urllib3.disable_warnings()

    logger = get_logger("checker_main")

    # Try to read from filesystem
    with open('/var/run/secrets/kubernetes.io/serviceaccount/token', 'r') as f:
        args.token = str(f.read()).strip()

    kube_apiserver_host = get_env('INFRABOX_KUBERNETES_MASTER_HOST')    
    kube_apiserver_port = get_env('INFRABOX_KUBERNETES_MASTER_PORT')

    args.api_server = "https://" + kube_apiserver_host + ":" + kube_apiserver_port

    conn = connect_db()
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    is_monitoring_enabled = get_env("INFRABOX_MONITORING_ENABLED") == 'true'

    if is_monitoring_enabled:
        logger.info("Monitoring enabled. Starting HTTP server for metrics")
        server_port = os.environ.get('INFRABOX_PORT', 8080)
        start_http_server(server_port)

    checker = Checker(conn, args)
    checker.run()

if __name__ == '__main__':
    main()
