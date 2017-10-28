import os
import sys
import requests

from infrabox_job.process import Failure

class Job(object):
    def __init__(self):
        self.api_server = os.environ.get("INFRABOX_JOB_API_URL", None)

        if not self.api_server:
            print "INFRABOX_JOB_API_URL not set"
            sys.exit(1)

        r = requests.get("%s/job" % self.api_server, headers=self.get_headers(), timeout=10)

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

        if 'source_upload' in data:
            self.source_upload = data['source_upload']

        self.deployments = data['deployments']

    def get_headers(self):
        return {
            'x-infrabox-token': os.environ['INFRABOX_JOB_API_TOKEN']
        }

    def create_jobs(self, jobs):
        payload = {
            "jobs": jobs,
        }

        r = requests.post("%s/create_jobs" % self.api_server,
                          headers=self.get_headers(),
                          json=payload, timeout=60)

        if r.status_code != 200:
            raise Failure(r.text)

    def set_running(self):
        requests.post("%s/setrunning" % self.api_server,
                      headers=self.get_headers(),
                      timeout=60).json()

    def set_finished(self, state):
        payload = {
            "state": state
        }
        requests.post("%s/setfinished" % self.api_server,
                      headers=self.get_headers(),
                      json=payload, timeout=60).json()

    def post_stats(self, stat):
        payload = {
            "stats": stat
        }
        requests.post("%s/stats" % self.api_server,
                      headers=self.get_headers(),
                      json=payload, timeout=60).json()

    def get_file_from_api_server(self, url, path):
        r = requests.get("%s%s" % (self.api_server, url),
                         headers=self.get_headers(),
                         timeout=600, stream=True)
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
        r = requests.post("%s%s" % (self.api_server, url),
                          headers=self.get_headers(),
                          files=files, timeout=600)

        if r.status_code != 200:
            raise Failure('Failed to upload file: %s' % r.text)

    def update_status(self, status):
        if status == "running":
            return self.set_running()

        return self.set_finished(status)
