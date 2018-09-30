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



class Checker(object):
    def __init__(self, conn, args):
        self.conn = conn
        self.args = args
        self.namespace = get_env("INFRABOX_GENERAL_SYSTEM_NAMESPACE")
        self.check_interval = int(get_env('INFRABOX_HA_CHECK_INTERVAL'))
        self.active_timeout = get_env('INFRABOX_HA_ACTIVE_TIMEOUT')
        self.cluster_name = get_env('INFRABOX_CLUSTER_NAME')
        self.logger = get_logger("checker")
        self.root_url =  get_env("INFRABOX_ROOT_URL")
        self.is_active = True
        self.check_result = True
        self.retry_times = 0
        self.max_retry_times = 3

    def _set_status(self, status):
        if self.is_active != status:
            self.is_active = status
            self.retry_times = 0
        self.retry_times += 1

    def check_dashboard(self):
        self.logger.debug('check dashboard')
        try:
            r = requests.head(self.root_url, verify=False, timeout=5)
            self.logger.debug("http return status code: %d" % r.status_code)
            if r.status_code != 200:
                self.check_result = False
            self.logger.debug("check dashboard result: %s, retry times %s" % \
                              (self.check_result, self.retry_times))
        except Exception as e:
            self.logger.exception('Got exception on check dashboard')
            self.check_result = False

    def check_api(self):
        self.logger.debug('check api ping')
        try:
            r = requests.head(self.root_url + '/api/ping', verify=False, timeout=5)
            self.logger.debug("http return status code: %d" % r.status_code)
            if r.status_code != 200:
                self.check_result = False
            self.logger.debug("check api result: %s, retry times %s" % \
                              (self.check_result, self.retry_times))
        except Exception as e:
            self.logger.exception('Got exception on check api')
            self.check_result = False

    def check_pods(self):
        self.logger.debug('check pods')
        try:
            h = {'Authorization': 'Bearer %s' % self.args.token}
            r = requests.get(
                self.args.api_server + '/api/v1/namespaces/%s/pods' % self.namespace,
                headers=h, timeout=10, verify=False)
            if r.status_code != 200:
                self.check_result = False
                self.logger.debug('check pods requests response http code: %d' % r.status_code)
                return
            pods = r.json()['items']
            for pod in pods:
                if pod['status']['phase'] not in ['Running', 'Succeeded']:
                    self.logger.debug('pod %s is in %s status' % \
                                     (pod['metadata']['name'], pod['status']['phase']))
                    self.check_result = False
                    return
            self.logger.debug('all pods are Running')
        except Exception as e:
            self.logger.exception('Got exception on check pods')
            self.check_result = False


    def check_storage(self):
        self.logger.debug("check storage")
        contents = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(15))
        file_name = "checker_test_"+ str(uuid.uuid4())
        path = "/tmp/" + file_name
        download_path = ""
        with open(path, 'w') as f:
            f.write(contents)
        try:
            with open(path, 'rb') as f:
                storage.upload_cache(f, file_name)

            self.logger.debug("upload file %s" % \
                             path)

            download_path = storage.download_cache(file_name)

            self.logger.debug("download file %s" % \
                              download_path)
        except Exception as e:
            self.logger.exception('Got exception on check storage')
            self.check_result = False

        finally:
            self.logger.debug("check api result: %s, retry times %s" % \
                              (self.check_result, self.retry_times))
            for f in [path, download_path]:
                if os.path.exists(f):
                    os.remove(f)
            storage.delete_cache(file_name)


    def self_check(self):
        self.check_result = True

        self.check_pods()
        self.check_dashboard()
        self.check_api()
        self.check_storage()

        self._set_status(self.check_result)

        if self.retry_times >= self.max_retry_times:
            self.retry_times = 0
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE cluster SET active=%s
                WHERE name=%s
            """,[self.is_active, self.cluster_name])
            cursor.close()
            self.logger.info("Set cluster %s active to %s. Reason: self check" % (self.cluster_name, self.is_active))

    def update_status(self):
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
            self.logger.info("Set cluster %s to inactive. Reason: last update time is too old" % c[0])

    def run(self):
        self.logger.info("Starting checker")

        while True:
            self.self_check()
            self.update_status()
            time.sleep(self.check_interval)


def main():
    # Arguments
    parser = argparse.ArgumentParser(prog="checker.py")
    args = parser.parse_args()

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

    # try to read from filesystem
    with open('/var/run/secrets/kubernetes.io/serviceaccount/token', 'r') as f:
        args.token = str(f.read()).strip()

    args.api_server = "https://" + get_env('INFRABOX_KUBERNETES_MASTER_HOST') \
                                 + ":" + get_env('INFRABOX_KUBERNETES_MASTER_PORT')


    conn = connect_db()
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    checker = Checker(conn, args)
    checker.run()

if __name__ == '__main__':
    main()
