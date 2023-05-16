import os
import unittest
import time
import subprocess
import json

import urllib3
import requests

def get_env(name: str):
    env = os.getenv(name)
    if not env:
        raise ValueError(f"env {name} not set")
    return env

INFRABOX_ROOT_URL = get_env("INFRABOX_ROOT_URL")

session = requests.Session()
urllib3.disable_warnings()

r = session.post(f"{INFRABOX_ROOT_URL}/api/v1/account/login", json={
    "email": get_env("INFRABOX_ADMIN_EMAIL"),
    "password": get_env("INFRABOX_ADMIN_PASSWORD"),
}, verify=False)

assert r.status_code == 200

def get_builds(project_id: str):
    r = session.get(f"{INFRABOX_ROOT_URL}/api/v1/projects/{project_id}/builds", verify=False)
    return r.json()


def get_latest_build(project_id: str):
    return get_builds(project_id)[0]


def get_jobs(project_id: str):
    build = get_latest_build(project_id)['id']
    r = session.get(f"{INFRABOX_ROOT_URL}/api/v1/projects/{project_id}/builds/{build}/jobs/", verify=False)
    return r.json()


def get_job(project_id: str, job_name):
    jobs = get_jobs(project_id)

    for j in jobs:
        if j['name'] == job_name:
            return j

    raise Exception('Job "%s" not found in: %s' % (job_name, jobs))



def print_build_logs(project_id: str):
    jobs = get_jobs(project_id)

    for j in jobs:
        r = session.get(f"{INFRABOX_ROOT_URL}/api/v1/projects/{project_id}/jobs/{j['id']}/console", verify=False)

        print(r.text)


def wait_latest_build(project_id: str):
    while True:
        print("polling build status...")
        jobs = get_jobs(project_id)

        active = False
        for j in jobs:
            if j['state'] not in ('finished', 'error', 'killed', 'skipped', 'failure'):
                active = True

        if not active:
            return

        time.sleep(5)


def run_build(cwd: str, project_id: str, cli_token: str):
    command = ['/home/cjc/.local/bin/infrabox', '--ca-bundle', 'False', "--url", INFRABOX_ROOT_URL , 'push']

    r = subprocess.run(command, cwd=cwd, env={"INFRABOX_CLI_TOKEN": cli_token}, check=True)

    wait_latest_build(project_id)
    print_build_logs(project_id)

class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        urllib3.disable_warnings()  # this is needed.. otherwise the warning still fires..

        # in case the old project did not get deleted
        try:
            r = session.get(f"{INFRABOX_ROOT_URL}/api/v1/projects/name/e2e-test", verify=False)
            project_id = r.json()['id']
            r = session.delete(f"{INFRABOX_ROOT_URL}/api/v1/projects/{project_id}", verify=False)
        except:
            pass

        r = session.post(f"{INFRABOX_ROOT_URL}/api/v1/projects", verify=False, json={
            "name": "e2e-test",
            "type": "upload",
            "private": False,
        })
        assert r.status_code == 200
        r = session.get(f"{INFRABOX_ROOT_URL}/api/v1/projects/name/e2e-test", verify=False)
        assert r.status_code == 200
        cls.project_id = r.json()['id']

        # create a new token for infrabox cli to use
        r = session.post(f"{INFRABOX_ROOT_URL}/api/v1/projects/{cls.project_id}/tokens", verify=False, json={
            "description": "e2e-test",
            "scope_pull": True,
            "scope_push": True,
        })
        assert r.status_code == 200
        cls.cli_token = r.json()['data']['token']

    def expect_job(self, job_name, state='finished', message=None, parents=None, dockerfile=None):
        j = get_job(self.project_id, job_name)
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

    def test_docker_job(self):
        run_build("./tests/docker_job", self.project_id, self.cli_token)
        self.expect_job('test')

    def test_docker_multiple_jobs(self):
        run_build('./tests/docker_multiple_jobs', self.project_id, self.cli_token)
        self.expect_job('test-1', parents=['Create Jobs'])
        self.expect_job('test-2', parents=['Create Jobs'])
        self.expect_job('test-3', parents=['Create Jobs'])
        self.expect_job('test-4', parents=['test-1', 'test-2'])
        self.expect_job('test-5', parents=['test-2', 'test-3'])

    def test_workflow_nested(self):
        run_build('./tests/workflow_nested', self.project_id, self.cli_token)
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

    @unittest.skip("FIXME: alpine apk add will hang forever..")
    def test_docker_compose_job(self):
        run_build('./tests/docker_compose_job', self.project_id, self.cli_token)
        self.expect_job('test')

    def test_docker_job_archive(self):
        run_build('./tests/docker_job_archive', self.project_id, self.cli_token)
        self.expect_job('test')

    def test_docker_compose_invalid_compose_file(self):
        run_build('./tests/docker_compose_invalid_compose_file', self.project_id, self.cli_token)
        self.expect_job('Create Jobs',
                        state='error',
                        message='version not found')

    def test_failed_job(self):
        run_build('./tests/failed_job', self.project_id, self.cli_token)
        self.expect_job('test', state='failure')

    def test_malicious_job(self):
        run_build('./tests/malicious_job', self.project_id, self.cli_token)
        self.expect_job('test')

    def test_workflow_recursive(self):
        run_build('./tests/workflow_recursive', self.project_id, self.cli_token)
        self.expect_job('Create Jobs', state='error', message='Recursive include detected')

    def test_workflow_simple_job(self):
        run_build('./tests/workflow_simple_job', self.project_id, self.cli_token)
        self.expect_job('flow', parents=['flow/test-sub'])
        self.expect_job('flow/test-sub', parents=['Create Jobs'])

    def test_image_input_output(self):
        run_build('./tests/docker_image_input_output', self.project_id, self.cli_token)
        self.expect_job('consumer')

    def test_input_output(self):
        run_build('./tests/docker_input_output', self.project_id, self.cli_token)
        self.expect_job('consumer')

    def test_infrabox_context(self):
        run_build('./tests/infrabox_context', self.project_id, self.cli_token)
        self.expect_job('root')
        self.expect_job('sub1')
        self.expect_job('sub1/sub1')

    # def test_secure_env(self):
    #     run_build('./tests/docker_secure_env', self.project_id, self.cli_token)
    #     self.expect_job('test')

    def test_secure_env_not_found(self):
        run_build('./tests/docker_secure_env_not_found', self.project_id, self.cli_token)
        self.expect_job('Create Jobs', state='error', message="Secret 'UNKNOWN_SECRET' not found")

    def test_insecure_env(self):
        run_build('./tests/docker_insecure_env', self.project_id, self.cli_token)
        self.expect_job('test')

    def test_infrabox_yaml(self):
        run_build('./tests/infrabox_yaml', self.project_id, self.cli_token)
        self.expect_job('hello-world')

    # TODO: test restart job / rerun job

    @classmethod
    def tearDownClass(cls):
        r = session.delete(f"{INFRABOX_ROOT_URL}/api/v1/projects/{cls.project_id}", verify=False)
        assert r.status_code == 200

if __name__ == "__main__":
    unittest.main()