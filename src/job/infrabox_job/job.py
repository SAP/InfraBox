import os
import sys
import requests

# pylint: disable=import-error,dangerous-default-value
from infrabox_job.process import Failure

class Job(object):
    def __init__(self):
        self.api_server = os.environ.get("INFRABOX_API_SERVER")

        if not self.api_server:
            print "INFRABOX_API_SERVER not set"
            sys.exit(1)

        r = requests.get("http://%s/job" % self.api_server, timeout=10)

        if r.status_code != 200:
            print "Stopping, API Server returned error code %s" % r.status_code
            sys.exit(0)

        data = r.json()
        self.job = data['job']
        self.project = data['project']
        self.build = data['build']
        self.repository = data['repository']
        self.commit = data['commit']
        self.dependencies = data['dependencies']
        self.parents = data['parents']
        self.environment = data['environment']
        self.quota = data['quota']

        if 'source_upload' in data:
            self.source_upload = data['source_upload']

        self.deployments = data['deployments']

    def create_github_commit_status(self, state, name):
        payload = {
            "state": state,
            "name": name
        }
        requests.post("http://%s/commitstatus" % self.api_server, json=payload, timeout=60).json()
        return 0

    def create_jobs(self, jobs):
        payload = {
            "jobs": jobs,
        }

        r = requests.post("http://%s/create_jobs" % self.api_server, json=payload, timeout=60)

        if r.status_code != 200:
            raise Failure(r.text)

        return 0

    def set_running(self):
        requests.post("http://%s/setrunning" % self.api_server, timeout=60).json()
        return 0

    def set_finished(self, state):
        payload = {
            "state": state
        }
        requests.post("http://%s/setfinished" % self.api_server, json=payload, timeout=60).json()
        return 0

    def post_stats(self, stat):
        payload = {
            "stats": stat
        }
        requests.post("http://%s/stats" % self.api_server, json=payload, timeout=60).json()
        return 0

    def get_file_from_api_server(self, url, path):
        r = requests.get("http://%s%s" % (self.api_server, url), timeout=600, stream=True)
        if r.status_code == 404:
            return

        if r.status_code != 200:
            raise Failure('Failed to download file: %s' % r.text)

        with open(path, 'wb') as  f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

    def post_file_to_api_server(self, url, path):
        files = {'data': open(path, 'rb')}
        r = requests.post("http://%s%s" % (self.api_server, url), files=files, timeout=600)

        if r.status_code != 200:
            raise Failure('Failed to upload file: %s' % r.text)

    def update_status(self, status):
        if status == "running":
            return self.set_running()

        return self.set_finished(status)
