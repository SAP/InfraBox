import os
import sys
import copy
import time
import requests

from infrabox_job.process import Failure

class Job(object):
    def __init__(self):
        self.api_server = os.environ.get("INFRABOX_JOB_API_URL", None)
        self.verify = True

        if os.environ.get('INFRABOX_GENERAL_DONT_CHECK_CERTIFICATES', 'false') == 'true':
            self.verify = False

        if not self.api_server:
            print "INFRABOX_JOB_API_URL not set"
            sys.exit(1)

        self.job = None
        self.project = None
        self.build = None
        self.repository = None
        self.commit = None
        self.dependencies = None
        self.parents = None
        self.environment = None
        self.env_vars = None
        self.secrets = None
        self.source_upload = None
        self.deployments = None

    def load_data(self):
        while True:
            try:
                r = requests.get("%s/job" % self.api_server,
                                 headers=self.get_headers(),
                                 timeout=10,
                                 verify=self.verify)
                time.sleep(1)

                if r.status_code == 409:
                    sys.exit(0)
                elif r.status_code == 400:
                    raise Failure(r.text)
                elif r.status_code == 200:
                    break
                else:
                    # Retry on any other error
                    continue
            except Failure:
                raise
            except Exception as e:
                print e

        data = r.json()
        self.job = data['job']
        self.project = data['project']
        self.build = data['build']
        self.repository = data['repository']
        self.commit = data['commit']
        self.dependencies = data['dependencies']
        self.parents = data['parents']
        self.environment = copy.deepcopy(data['env_vars'])
        self.environment.update(data['secrets'])
        self.secrets = data['secrets']
        self.env_vars = data['env_vars']

        if 'source_upload' in data:
            self.source_upload = data['source_upload']

        self.deployments = data['deployments']

    def get_headers(self):
        return {
            'Authorization': 'token ' + os.environ['INFRABOX_JOB_TOKEN']
        }

    def create_jobs(self, jobs):
        if not jobs:
            return

        payload = {
            "jobs": jobs,
        }

        r = requests.post("%s/create_jobs" % self.api_server,
                          headers=self.get_headers(),
                          json=payload, timeout=60, verify=self.verify)

        if r.status_code != 200:
            msg = r.text
            try:
                msg = r.json()['message']
            except:
                pass

            raise Failure(msg)

    def post_api_server(self, endpoint, data=None):
        while True:
            try:
                r = requests.post("%s/%s" % (self.api_server, endpoint),
                                  headers=self.get_headers(),
                                  timeout=20,
                                  json=data,
                                  verify=self.verify)
                if r.status_code == 200:
                    return
            except Exception as e:
                print e

            time.sleep(1)

    def set_running(self):
        self.post_api_server('setrunning')

    def set_finished(self, state, message):
        payload = {
            'state': state,
            'message': message
        }

        self.post_api_server('setfinished', data=payload)

    def post_stats(self, stat):
        payload = {
            "stats": stat
        }

        self.post_api_server('stats', data=payload)

    def get_file_from_api_server(self, url, path):
        r = requests.get("%s%s" % (self.api_server, url),
                         headers=self.get_headers(),
                         timeout=600, stream=True, verify=self.verify)
        if r.status_code == 404:
            return

        if r.status_code != 200:
            raise Failure('Failed to download file: %s' % r.text)

        with open(path, 'wb') as  f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

    def post_file_to_api_server(self, url, path, filename=None):
        message = None

        if not filename:
            filename = os.path.basename(path)

        for _ in xrange(0, 5):
            files = {filename: open(path)}
            try:
                r = requests.post("%s%s" % (self.api_server, url),
                                  headers=self.get_headers(),
                                  files=files, timeout=600, verify=self.verify)
            except Exception as e:
                message = str(e)
                time.sleep(5)
                continue

            if r.status_code != 200:
                time.sleep(5)
                message = r.text

                try:
                    message = r.json()['message']
                except:
                    pass
            else:
                return

        raise Failure('Failed to upload file: %s' % message)

    def update_status(self, status, message=None):
        if status == "running":
            return self.set_running()

        return self.set_finished(status, message)
