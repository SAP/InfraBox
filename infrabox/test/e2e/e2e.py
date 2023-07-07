"""
Three envs should be set:
INFRABOX_ADMIN_EMAIL
INFRABOX_ADMIN_PASSWORD
INFRABOX_ROOT_URL
"""

import os
import unittest
import time
import subprocess
import json
import uuid
import re

import urllib3
import requests
import pytest


def get_env(name: str):
    env = os.getenv(name)
    if not env:
        raise ValueError(f"env {name} not set")
    return env


INFRABOX_ROOT_URL = get_env("INFRABOX_ROOT_URL")
E2E_PROJECT_NAME = "e2e-test"

session = requests.Session()
urllib3.disable_warnings()


def get_job(project_id: str, build_str: str, job_name):
    build = get_build(project_id, build_str)

    for j in build:
        if j["job"]["name"] == job_name:
            return j["job"]

    raise Exception('Job "%s" not found in: %s' % (job_name, build))


def get_build(project_id: str, build_str: str):
    url = f"{INFRABOX_ROOT_URL}/api/v1/projects/{project_id}/builds/{build_str}"
    r = session.get(url, verify=False)
    return r.json()


def print_build_logs(project_id: str, build_str: str):
    build = get_build(project_id, build_str)

    for job in build:
        r = session.get(
            f"{INFRABOX_ROOT_URL}/api/v1/projects/{project_id}/jobs/{job['job']['id']}/console",
            verify=False,
        )

        print(r.text)


def wait_latest_build(project_id: str, build_str: str):
    while True:
        print("polling build status...")
        build = get_build(project_id, build_str)

        active = False
        for job in build:
            if job["job"]["state"] not in (
                "finished",
                "error",
                "killed",
                "skipped",
                "failure",
            ):
                active = True

        if not active:
            return

        time.sleep(5)


def run_build(cwd: str, project_id: str, cli_token: str) -> str:
    """
    return value is a combined string of build_number and restart counter
    like 14/1
    """

    command = ["infrabox", "--ca-bundle", "False", "--url", INFRABOX_ROOT_URL, "push"]

    os.environ["INFRABOX_CLI_TOKEN"] = cli_token
    # we are not passing this env directly to subprocess.run since we want it to
    # inherit current envs (like PATH)
    r = subprocess.run(command, cwd=cwd, check=True, capture_output=True)
    print(r.stdout.decode())
    build_string = re.search(
        fr"{INFRABOX_ROOT_URL}/dashboard/#/project/{E2E_PROJECT_NAME}/build/(\d*/\d*)",
        r.stdout.decode(),
    )
    if not build_string:
        raise Exception("cannot match build numbers in the stdout of `infrabox push`")
    build_string = build_string.group(1)

    wait_latest_build(project_id, build_string)
    print_build_logs(project_id, build_string)

    return build_string


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        urllib3.disable_warnings()  # this is needed.. otherwise the warning still fires..

        # login
        r = session.post(
            f"{INFRABOX_ROOT_URL}/api/v1/account/login",
            json={
                "email": get_env("INFRABOX_ADMIN_EMAIL"),
                "password": get_env("INFRABOX_ADMIN_PASSWORD"),
            },
            verify=False,
        )

        assert r.status_code == 200

        # if e2e-test project does not exist, create it
        r = session.get(
            f"{INFRABOX_ROOT_URL}/api/v1/projects/name/{E2E_PROJECT_NAME}", verify=False
        )
        if r.status_code == 404:
            r = session.post(
                f"{INFRABOX_ROOT_URL}/api/v1/projects",
                verify=False,
                json={
                    "name": E2E_PROJECT_NAME,
                    "type": "upload",
                    "private": False,
                },
            )
            print(r.content)
            assert r.status_code == 200
            r = session.get(
                f"{INFRABOX_ROOT_URL}/api/v1/projects/name/{E2E_PROJECT_NAME}",
                verify=False,
            )
        cls.project_id = r.json()["id"]

        # create a new token for infrabox cli to use
        r = session.post(
            f"{INFRABOX_ROOT_URL}/api/v1/projects/{cls.project_id}/tokens",
            verify=False,
            json={
                "description": str(uuid.uuid1()),
                "scope_pull": True,
                "scope_push": True,
            },
        )
        print(r.content)
        assert r.status_code == 200
        cls.cli_token = r.json()["data"]["token"]

    def expect_job(
        self, job_name, state="finished", message=None, parents=None, dockerfile=None, console_contains=[]
    ):
        j = get_job(self.project_id, self.build_str, job_name)
        data = json.dumps(j, indent=4)

        self.assertEqual(j["state"], state, data)

        if message:
            self.assertIn(message, j["message"], data)

        if dockerfile:
            self.assertEqual(j["definition"]["docker_file"], dockerfile, data)

        if parents:
            actual_parents = {}
            for p in j.get("dependencies", []):
                actual_parents[p["job"]] = p

            for p in parents:
                self.assertTrue(p in actual_parents, data)

        if len(console_contains):
            r = session.get(
                f"{INFRABOX_ROOT_URL}/api/v1/projects/{self.project_id}/jobs/{j['id']}/console",
                verify=False,
            )
            
            for text in console_contains:
                assert text in r.text

    def test_docker_job(self):
        self.build_str = run_build(
            "./tests/docker_job", self.project_id, self.cli_token
        )
        self.expect_job("test", console_contains=["Hello World"])

    def test_docker_multiple_jobs(self):
        self.build_str = run_build(
            "./tests/docker_multiple_jobs", self.project_id, self.cli_token
        )
        self.expect_job("test-1", parents=["Create Jobs"])
        self.expect_job("test-2", parents=["Create Jobs"])
        self.expect_job("test-3", parents=["Create Jobs"])
        self.expect_job("test-4", parents=["test-1", "test-2"])
        self.expect_job("test-5", parents=["test-2", "test-3"])

    def test_workflow_nested(self):
        self.build_str = run_build(
            "./tests/workflow_nested", self.project_id, self.cli_token
        )
        self.expect_job("flow", parents=["flow/sub-2", "flow/sub-3"])
        self.expect_job(
            "flow/sub-1", parents=["Create Jobs"], dockerfile="Dockerfile_flow"
        )
        self.expect_job(
            "flow/sub-2", parents=["flow/sub-2/nested-2", "flow/sub-2/nested-3"]
        )

        self.expect_job(
            "flow/sub-2/nested-1",
            parents=["flow/sub-1"],
            dockerfile="Dockerfile_nested",
        )
        self.expect_job(
            "flow/sub-2/nested-2",
            parents=["flow/sub-2/nested-1"],
            dockerfile="Dockerfile_nested",
        )
        self.expect_job(
            "flow/sub-2/nested-3",
            parents=["flow/sub-2/nested-1"],
            dockerfile="Dockerfile_nested",
        )
        self.expect_job(
            "flow/sub-3", parents=["flow/sub-1"], dockerfile="Dockerfile_flow"
        )

    def test_docker_compose_job(self):
        self.build_str = run_build(
            "./tests/docker_compose_job", self.project_id, self.cli_token
        )
        self.expect_job("test")

    def test_docker_job_archive(self):
        self.build_str = run_build(
            "./tests/docker_job_archive", self.project_id, self.cli_token
        )
        self.expect_job("test")

    def test_docker_compose_invalid_compose_file(self):
        self.build_str = run_build(
            "./tests/docker_compose_invalid_compose_file",
            self.project_id,
            self.cli_token,
        )
        self.expect_job("Create Jobs", state="error", message="version not found")

    def test_failed_job(self):
        self.build_str = run_build(
            "./tests/failed_job", self.project_id, self.cli_token
        )
        self.expect_job("test", state="failure")

    def test_malicious_job(self):
        self.build_str = run_build(
            "./tests/malicious_job", self.project_id, self.cli_token
        )
        self.expect_job("test")

    def test_workflow_recursive(self):
        self.build_str = run_build(
            "./tests/workflow_recursive", self.project_id, self.cli_token
        )
        self.expect_job(
            "Create Jobs", state="error", message="Recursive include detected"
        )

    def test_workflow_simple_job(self):
        self.build_str = run_build(
            "./tests/workflow_simple_job", self.project_id, self.cli_token
        )
        self.expect_job("flow", parents=["flow/test-sub"])
        self.expect_job("flow/test-sub", parents=["Create Jobs"])

    def test_image_input_output(self):
        self.build_str = run_build(
            "./tests/docker_image_input_output", self.project_id, self.cli_token
        )
        self.expect_job("consumer")

    def test_input_output(self):
        self.build_str = run_build(
            "./tests/docker_input_output", self.project_id, self.cli_token
        )
        self.expect_job("consumer")

    def test_infrabox_context(self):
        self.build_str = run_build(
            "./tests/infrabox_context", self.project_id, self.cli_token
        )
        self.expect_job("root")
        self.expect_job("sub1")
        self.expect_job("sub1/sub1")

    def test_secure_env(self):
        r = session.post(
                f"{INFRABOX_ROOT_URL}/api/v1/projects/{self.project_id}/secrets",
                verify=False,
                json={
                    "name": "SECRET_ENV",
                    "value": "hello world",
                }
            )
        assert r.json()['message'] in ("Successfully added secret.", "Secret with this name already exist.")
        self.build_str = run_build('./tests/docker_secure_env', self.project_id, self.cli_token)
        self.expect_job('test')

    def test_secure_env_not_found(self):
        self.build_str = run_build(
            "./tests/docker_secure_env_not_found", self.project_id, self.cli_token
        )
        self.expect_job(
            "Create Jobs", state="error", message="Secret 'UNKNOWN_SECRET' not found"
        )

    def test_insecure_env(self):
        self.build_str = run_build(
            "./tests/docker_insecure_env", self.project_id, self.cli_token
        )
        self.expect_job("test")

    def test_infrabox_yaml(self):
        self.build_str = run_build(
            "./tests/infrabox_yaml", self.project_id, self.cli_token
        )
        self.expect_job("hello-world")

    def test_testresult_api(self):
        self.build_str = run_build(
            "./tests/infrabox_testresult", self.project_id, self.cli_token
        )
        job_name = "testresult"
        self.expect_job(job_name)
        j = get_job(self.project_id, self.build_str, job_name)
        r = session.get(
                f"{INFRABOX_ROOT_URL}/api/v1/projects/{self.project_id}/jobs/{j['id']}/testruns",
                verify=False,
            )
        test_choice = r.json()[0]
        test_skipped = r.json()[3]
        assert test_choice['name'] == "test_choice"
        assert test_choice['state'] == "ok"
        assert test_skipped['name'] == "test_skipped"
        assert test_skipped['state'] == "skipped"

    # TODO: test restart job / rerun job


if __name__ == "__main__":
    print("run with `pytest e2e.py -n x`, don't forget the envs")
