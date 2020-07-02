import unittest
import os
import subprocess
import logging
import re
import time
import json
import requests
import urllib3

import xmlrunner

from pyinfraboxutils.db import connect_db, DB
from pyinfraboxutils.token import encode_project_token
from pyinfraboxutils.secrets import encrypt_secret

class Test(unittest.TestCase):
    job_id = '1514af82-3c4f-4bb5-b1da-a89a0ced5e6f'
    user_id = '2514af82-3c4f-4bb5-b1da-a89a0ced5e6b'
    build_id = '3514af82-3c4f-4bb5-b1da-a89a0ced5e6a'
    project_id = '4514af82-3c4f-4bb5-b1da-a89a0ced5e6f'
    token_id = '5514af82-3c4f-4bb5-b1da-a89a0ced5e6f'

    def setUp(self):
        conn = connect_db()
        cur = conn.cursor()
        cur.execute('''DELETE FROM job''')
        cur.execute('''DELETE FROM auth_token''')
        cur.execute('''DELETE FROM collaborator''')
        cur.execute('''DELETE FROM project''')
        cur.execute('''DELETE FROM "user"''')
        cur.execute('''DELETE FROM source_upload''')
        cur.execute('''DELETE FROM build''')
        cur.execute('''DELETE FROM test_run''')
        cur.execute('''DELETE FROM measurement''')
        cur.execute('''DELETE FROM job_markup''')
        cur.execute('''DELETE FROM secret''')
        cur.execute('''INSERT INTO "user"(id, github_id, avatar_url, name,
                            email, github_api_token, username)
                        VALUES(%s, 1, 'avatar', 'name', 'email', 'token', 'login')''', (self.user_id,))
        cur.execute('''INSERT INTO project(name, type, id, public)
                        VALUES('test', 'upload', %s, true)''', (self.project_id,))
        cur.execute('''INSERT INTO collaborator(project_id, user_id, role)
                        VALUES(%s, %s, 'Owner')''', (self.project_id, self.user_id,))
        cur.execute('''INSERT INTO auth_token(project_id, id, description, scope_push, scope_pull)
                        VALUES(%s, %s, 'asd', true, true)''', (self.project_id, self.token_id,))
        cur.execute('''INSERT INTO secret(project_id, name, value)
                        VALUES(%s, 'SECRET_ENV', %s)''', (self.project_id, encrypt_secret('hello world')))
        conn.commit()

        os.environ['INFRABOX_CLI_TOKEN'] = encode_project_token(self.token_id, self.project_id, 'myproject')
        self.root_url = os.environ['INFRABOX_ROOT_URL']

    def _api_get(self, url):
        headers = {'Authorization': 'bearer ' + os.environ['INFRABOX_CLI_TOKEN']}
        retries = 600

        while True:
            try:
                return requests.get(url, headers=headers, verify=False)
            except Exception as e:
                logging.exception(e)
                time.sleep(1)
                retries -= 1

                if retries < 0:
                    raise e

    def _get_build(self):
        url = '%s/api/v1/projects/%s/builds/' % (self.root_url, self.project_id)
        result = self._api_get(url)
        try:
            return result.json()[0]
        except:
            print("Get build failed: ")
            print(result.text)
            raise

    def _get_jobs(self):
        build = self._get_build()
        url = '%s/api/v1/projects/%s/builds/%s/jobs/' % (self.root_url, self.project_id, build['id'])
        jobs = self._api_get(url)

        try:
            return jobs.json()
        except:
            print("Get jobs failed: ")
            print(jobs)
            raise

    def _wait_build(self):
        while True:
            jobs = self._get_jobs()

            active = False
            for j in jobs:
                if j['state'] not in ('finished', 'error', 'killed', 'skipped', 'failure'):
                    active = True

            if not active:
                return

            time.sleep(3)

    def _print_job_logs(self):
        self._wait_build()
        jobs = self._get_jobs()

        for j in jobs:
            url = '%s/api/v1/projects/%s/jobs/%s/console' % (self.root_url,
                                                             self.project_id,
                                                             j['id'])
            r = self._api_get(url)

            ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
            logs = ansi_escape.sub('', r.text)

            print(logs)

    def _get_job(self, job_name):
        jobs = self._get_jobs()

        for j in jobs:
            data = json.dumps(j, indent=4)
            if j['name'] == job_name:
                return j

        data = json.dumps(jobs, indent=4)
        raise Exception('Job "%s" not found in: %s' % (job_name, data))

    def _wait_job(self, job_name):
        while True:
            j = self._get_job(job_name)

            if j['state'] in ('finished', 'error', 'killed', 'skipped', 'failure'):
                return j

            time.sleep(5)

    def expect_job(self, job_name, state='finished', message=None, parents=None, dockerfile=None):
        j = self._get_job(job_name)
        data = json.dumps(j, indent=4)

        self.assertEqual(j['state'], state, data)

        if message:
            self.assertIn(message, j['message'], data)

        if dockerfile:
            self.assertEqual(j['docker_file'], dockerfile, data)

        if parents:
            actual_parents = {}
            for p in j.get('depends_on', []):
                actual_parents[p['job']] = p

            for p in parents:
                self.assertTrue(p in actual_parents, data)

    def restart_job(self, restart_job_name):
        #/api/v1/projects/{PROJECT_ID}/jobs/{INFRABOX_JOB_ID}/restart
        jobs = self._get_jobs()
        for j in jobs:
            if j['name'] == restart_job_name:
                url = '%s/api/v1/projects/%s/jobs/%s/restart' % (self.root_url, self.project_id, j['id'])
                r = self._api_get(url)
                try:
                    if r.status_code == 200 and r.json()['status'] == 200:
                        return True
                except:
                    print("restart job failed: ")
                    print(r)
                    raise
        return False

    def rerun_job(self, rerun_job_name):
        #/api/v1/projects/{PROJECT_ID}/jobs/{INFRABOX_JOB_ID}/rerun
        jobs = self._get_jobs()
        for j in jobs:
            if j['name'] == rerun_job_name:
                url = '%s/api/v1/projects/%s/jobs/%s/rerun' % (self.root_url, self.project_id, j['id'])
                r = self._api_get(url)
                try:
                    if r.status_code == 200 and r.json()['status'] == 200:
                        return True
                except:
                    print("rerun job failed: ")
                    print(r)
                    raise
        return False

    def run_it(self, cwd):
        command = ['infrabox', '--ca-bundle', 'false', 'push']
        output = None

        while True:
            try:
                output = subprocess.check_output(command, cwd=cwd)
                break
            except subprocess.CalledProcessError as e:
                output = e.output
                print(output)
                time.sleep(5)

        self._print_job_logs()

    #def test_docker_job(self):
    #    self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_job')
    #    self.expect_job('test')

    def test_docker_multiple_jobs(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_multiple_jobs')
        self.expect_job('test-1', parents=['Create Jobs'])
        self.expect_job('test-2', parents=['Create Jobs'])
        self.expect_job('test-3', parents=['Create Jobs'])
        self.expect_job('test-4', parents=['test-1', 'test-2'])
        self.expect_job('test-5', parents=['test-2', 'test-3'])

    def test_workflow_nested(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/workflow_nested')
        self.expect_job('flow', parents=['flow/sub-2', 'flow/sub-3'])
        self.expect_job('flow/sub-1', parents=['Create Jobs'], dockerfile='Dockerfile_flow')
        self.expect_job('flow/sub-2', parents=['flow/sub-2/nested-2', 'flow/sub-2/nested-3'])

        self.expect_job('flow/sub-2/nested-1',
                        parents=['flow/sub-1'],
                        dockerfile='Dockerfile_nested')
        self.expect_job('flow/sub-2/nested-2',
                        parents=['flow/sub-2/nested-1'],
                        dockerfile='Dockerfile_nested')
        self.expect_job('flow/sub-2/nested-3',
                        parents=['flow/sub-2/nested-1'],
                        dockerfile='Dockerfile_nested')
        self.expect_job('flow/sub-3',
                        parents=['flow/sub-1'],
                        dockerfile='Dockerfile_flow')


    def test_docker_compose_job(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_compose_job')
        self.expect_job('test')

    def test_docker_job_archive(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_job_archive')
        self.expect_job('test')

    def test_docker_compose_invalid_compose_file(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_compose_invalid_compose_file')
        self.expect_job('Create Jobs',
                        state='error',
                        message='version not found')

    def test_failed_job(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/failed_job')
        self.expect_job('test', state='failure')

    def test_malicious_job(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/malicious_job')
        self.expect_job('test')

    def test_workflow_recursive(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/workflow_recursive')
        self.expect_job('Create Jobs', state='error', message='Recursive include detected')

    def test_workflow_simple_job(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/workflow_simple_job')
        self.expect_job('flow', parents=['flow/test-sub'])
        self.expect_job('flow/test-sub', parents=['Create Jobs'])

    def test_image_input_output(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_image_input_output')
        self.expect_job('consumer')

    def test_input_output(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_input_output')
        self.expect_job('consumer')

    def test_infrabox_context(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/infrabox_context')
        self.expect_job('root')
        self.expect_job('sub1')
        self.expect_job('sub1/sub1')

    def test_secure_env(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_secure_env')
        self.expect_job('test')

    def test_secure_env_not_found(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_secure_env_not_found')
        self.expect_job('Create Jobs', state='error', message="Secret 'UNKNOWN_SECRET' not found")

    def test_insecure_env(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_insecure_env')
        self.expect_job('test')

    def test_infrabox_yaml(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/infrabox_yaml')
        self.expect_job('hello-world')

    def test_restart_job(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/test_restart_job')
        # restart a job and its children
        self.expect_job('test-2')
        self.restart_job('test-1')
        time.sleep(90)
        self.expect_job('test-2.1', parents=['test-1.1'])

    def test_rerun_job(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/test_restart_job')
        # restart a single job
        self.rerun_job('test-1')
        time.sleep(90)
        self.expect_job('test-1.1')
        self.expect_job('test-2', parents=['test-1.1'])

def main():

    root_url = os.environ['INFRABOX_ROOT_URL']

    urllib3.disable_warnings()

    print("Connecting to DB")
    connect_db() # Wait for DB

    print("ROOT_URL: %s" % root_url)
    while True:
        time.sleep(1)
        r = None
        try:
            r = requests.get(root_url, verify=False)

            if r.status_code in (200, 404):
                break

            print(r.text)
        except Exception as e:
            print(e)

        print("Server not yet ready")

    time.sleep(90)

    print("Starting tests")
    with open('results.xml', 'wb') as output:
        unittest.main(testRunner=xmlrunner.XMLTestRunner(output=output), buffer=False)

if __name__ == '__main__':
    main()
