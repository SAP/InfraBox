import os
import sys
import json
import glob
import copy
import time
import shutil
import requests

from infrabox_job.process import Failure, Error

class Job(object):
    def __init__(self):
        self.api_server =  "http://infrabox-api." + os.environ["INFRABOX_GENERAL_SYSTEM_NAMESPACE"] + ":8080/api/job"
        self.verify = False

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
        self.registries = None
        self.github_host = os.environ.get('GITHUB_HOST', "")
        self.enable_token_access = os.environ.get('GITHUB_ENABLE_TOKEN_ACCESS', False)
        self.aborted = False

    def load_data(self):
        retry = 0
        current_backoff = 1
        backoff_limit = 300

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
                    msg = r.text

                    try:
                        msg = r.json()['message']
                    except:
                        pass

                    raise Error(msg)
                elif r.status_code == 200:
                    break
                else:
                    # exponential backoff
                    if retry < 10:
                        retry += 1
                        if current_backoff < backoff_limit:
                            backoff = current_backoff
                            current_backoff *= 2
                        else:
                            backoff = backoff_limit
                        time.sleep(backoff)
                        continue
                    else:
                        raise Error(r.text)
            except Error as e:
                raise e
            except Exception as e:
                print(e)

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
        self.registries = data['registries']

        if 'source_upload' in data:
            self.source_upload = data['source_upload']

        self.deployments = data['deployments']

        self.enable_token_access = self.enable_token_access and self.repository.get('github_api_token', None)

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

        while True:
            try:
                r = requests.post("%s/create_jobs" % self.api_server,
                                  headers=self.get_headers(),
                                  json=payload, timeout=300, verify=self.verify)
            except:
                self.console.collect('Failed to connect to API, retrying.', show=True)
                time.sleep(3)
                continue

            if r.status_code == 200:
                return

            if r.status_code == 400:
                msg = r.text
                try:
                    msg = r.json()['message']
                except:
                    pass

                raise Error(msg)

            self.console.collect('Failed to connect to API, retrying.', show=True)
            time.sleep(3)

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
                print(e)

            self.console.collect('Failed to connect to API, retrying.', show=True)
            time.sleep(1)

    def post_stats(self, stat):
        payload = {
            "stats": stat
        }

        self.post_api_server('stats', data=payload)

    def get_file_from_api_server(self, url, path, split=False):
        if split:
            if os.path.isfile('/tmp/output.json'):
                os.remove('/tmp/output.json')

            self._get_file_from_api_server(url + "?filename=output.json", '/tmp/output.json')

            if not os.path.isfile('/tmp/output.json'):
                return

            with open('/tmp/output.json') as filelist:
                files = json.load(filelist)

            if os.path.exists('/tmp/output'):
                shutil.rmtree('/tmp/output')

            os.makedirs('/tmp/output/parts')

            with open(path, 'w+b') as final:
                for f in files:
                    self._get_file_from_api_server(url + "?filename=" + f, '/tmp/output/parts/%s' % f)

                    with open('/tmp/output/parts/%s' % f, 'rb') as part:
                        shutil.copyfileobj(part, final, 1024*1024*10)

                    os.remove('/tmp/output/parts/%s' % f)

            shutil.rmtree('/tmp/output')
        else:
            self._get_file_from_api_server(url, path)

    def _get_file_from_api_server(self, url, path):
        self.console.collect('Downloading %s' % path, show=True)

        message = None

        r = None
        for _ in range(0, 20):
            try:
                message = None
                r = requests.get("%s%s" % (self.api_server, url),
                                 headers=self.get_headers(),
                                 timeout=600, stream=True, verify=self.verify)

                if r.status_code == 404:
                    return

                if r.status_code != 200:
                    self.console.collect('Failed to download file (%s), retrying' % r.status_code, show=True)
                    time.sleep(10)
                    continue

                with open(path, 'wb') as  f:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                return

            except Exception as e:
                message = str(e)
                self.console.collect('Failed to download file (%s), retrying' % message, show=True)
                time.sleep(10)
                continue

        if message:
            raise Error('Failed to download file: %s' % message)

        if r.status_code != 200:
            msg = r.text

            try:
                msg = r.json()['message']
            except:
                pass

            raise Error('Failed to download file(%s): %s' % (r.status_code, msg))

    def post_file_to_api_server(self, url, path, filename=None, split=False):
        if not filename:
            filename = os.path.basename(path)

        if split:
            self.console.execute(["split", "-b", "64m", path, path + "-"], show=True)
            files = glob.glob(path + "-*")
            files.sort()

            filenames = []
            for f in files:
                filenames.append(os.path.basename(f))

            with open('/tmp/files.json', 'w') as out:
                json.dump(filenames, out)

            self._post_file_to_api_server(url, '/tmp/files.json', 'output.json')

            for f in files:
                self._post_file_to_api_server(url, f, os.path.basename(f))
        else:
            self._post_file_to_api_server(url, path, filename)

    def _post_file_to_api_server(self, url, path, filename):
        self.console.collect('Uploading %s' % path, show=True)

        message = None
        retry_time = 10

        for _ in range(0, 5):
            message = None
            files = {filename: open(path, "rb")}
            try:
                r = requests.post("%s%s" % (self.api_server, url),
                                  headers=self.get_headers(),
                                  files=files, timeout=600, verify=self.verify)
            except Exception as e:
                message = str(e)
                retry_time *= 2
                time.sleep(retry_time)
                continue

            if r.status_code != 200:
                retry_time *= 2
                time.sleep(retry_time)
                message = r.text

                try:
                    message = r.json()['message']
                except:
                    pass
            else:
                return

        raise Error('Failed to upload file: %s' % message)
