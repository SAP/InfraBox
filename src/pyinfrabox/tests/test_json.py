import unittest

from pyinfrabox import ValidationError
from pyinfrabox.infrabox import validate_json

class TestDockerCompose(unittest.TestCase):
    def raises_expect(self, data, expected):
        try:
            validate_json(data)
            assert False
        except ValidationError as e:
            self.assertEqual(e.message, expected)

    def test_version(self):
        self.raises_expect({}, "#: property 'version' is required")
        self.raises_expect({'version': 'asd', 'jobs': []}, "#version: must be an int")
        self.raises_expect({'version': '1', 'jobs': []}, "#version: must be an int")
        self.raises_expect({'version': 2, 'jobs': []}, "#version: unsupported version")

    def test_jobs(self):
        self.raises_expect({'version': 1, 'jobs': 'asd'}, "#jobs: must be an array")
        self.raises_expect({'version': 1, 'jobs': [{}]}, "#jobs[0]: does not contain a 'type'")

    def test_empty_jobs(self):
        validate_json({'version': 1, 'jobs': []})

    def test_dep_defined_later(self):
        d = {
            "version": 1,
            "jobs": [{
                "type": "docker",
                "name": "source",
                "docker_file": "Dockerfile",
                "resources": {"limits": {"cpu": 1, "memory": 1024}},
                "build_only": False,
                "depends_on": ["compile"]
            }, {
                "type": "docker",
                "name": "compile",
                "docker_file": "Dockerfile",
                "build_only": False,
                "resources": {"limits": {"cpu": 1, "memory": 1024}},
            }]
        }

        self.raises_expect(d, "#jobs[0].depends_on: Job 'compile' not found")

    def test_dep_not_found(self):
        d = {
            "version": 1,
            "jobs": [{
                "type": "docker",
                "name": "compile",
                "docker_file": "test/Dockerfile_benchmarks",
                "resources": {"limits": {"cpu": 1, "memory": 1024}},
                "build_only": False,
                "depends_on": ["not_found"]
            }]
        }

        self.raises_expect(d, "#jobs[0].depends_on: Job 'not_found' not found")

    def test_deps_must_be_unique(self):
        d = {
            "version": 1,
            "jobs": [{
                "type": "docker",
                "name": "source",
                "docker_file": "Dockerfile",
                "build_only": False,
                "resources": {"limits": {"cpu": 1, "memory": 1024}},
            }, {
                "type": "docker",
                "name": "compile",
                "docker_file": "Dockerfile",
                "build_only": False,
                "resources": {"limits": {"cpu": 1, "memory": 1024}},
                "depends_on": ["source", "source"]
            }]
        }

        self.raises_expect(d, "#jobs[1].depends_on: 'source' duplicate dependencies")

    def test_duplicate_job_name(self):
        d = {
            "version": 1,
            "jobs": [{
                "type": "docker",
                "name": "compile",
                "docker_file": "test/Dockerfile_benchmarks",
                "build_only": False,
                "resources": {"limits": {"cpu": 1, "memory": 1024}},
            }, {
                "type": "docker",
                "name": "compile",
                "docker_file": "test/Dockerfile_benchmarks",
                "resources": {"limits": {"cpu": 1, "memory": 1024}},
                "build_only": False,
                "depends_on": ["compile"]
            }]
        }

        self.raises_expect(d, "#jobs[1].name: Job name 'compile' already exists")

    def test_dependency_conditions(self):
        d = {
            "version": 1,
            "jobs": [{
                "type": "docker",
                "name": "compile",
                "docker_file": "test/Dockerfile_benchmarks",
                "build_only": False,
                "resources": {"limits": {"cpu": 1, "memory": 1024}},
            }, {
                "type": "docker",
                "name": "compile2",
                "docker_file": "test/Dockerfile_benchmarks",
                "resources": {"limits": {"cpu": 1, "memory": 1024}},
                "build_only": False,
                "depends_on": [{"job": "compile", "on": True}]
            }]
        }

        self.raises_expect(d, "#jobs[1].depends_on[0].on: must be a list")

        d['jobs'][1]['depends_on'] = [{"job": "compile", "on": []}]
        self.raises_expect(d, "#jobs[1].depends_on[0].on: must not be empty")

        d['jobs'][1]['depends_on'] = [{"job": "compile", "on": [True]}]
        self.raises_expect(d, "#jobs[1].depends_on[0].on: True is not a valid value")

        d['jobs'][1]['depends_on'] = [{"job": "compile", "on": ["not valid"]}]
        self.raises_expect(d, "#jobs[1].depends_on[0].on: not valid is not a valid value")

        d['jobs'][1]['depends_on'] = [{"job": "not-valid", "on": ["*"]}]
        self.raises_expect(d, "#jobs[1].depends_on: Job 'not-valid' not found")

        d['jobs'][1]['depends_on'] = [{"job": "compile", "on": ["error", "error"]}]
        self.raises_expect(d, "#jobs[1].depends_on[0].on: error used twice")


    def test_empty_dep_array(self):
        d = {
            "version": 1,
            "jobs": [{
                "type": "docker",
                "name": "compile",
                "docker_file": "test/Dockerfile_benchmarks",
                "resources": {"limits": {"cpu": 1, "memory": 1024}},
                "build_only": False,
                "depends_on": []
            }]
        }

        self.raises_expect(d, "#jobs[0].depends_on: must not be empty")

    def test_invalid_name(self):
        d = {
            "version": 1,
            "jobs": [{
                "type": "docker",
                "name": "../blub",
                "docker_file": "Dockerfile",
                "build_only": False,
                "resources": {"limits": {"cpu": 1, "memory": 1024}},
            }]
        }

        self.raises_expect(d, "#jobs[0].name: '../blub' not a valid value")

        d = {
            "version": 1,
            "jobs": [{
                "type": "docker",
                "name": "blub'",
                "docker_file": "Dockerfile",
                "build_only": False,
                "resources": {"limits": {"cpu": 1, "memory": 1024}},
            }]
        }

        self.raises_expect(d, "#jobs[0].name: 'blub\'' not a valid value")

    def test_may_not_depend_on_itself(self):
        d = {
            "version": 1,
            "jobs": [{
                "type": "docker",
                "name": "compile",
                "docker_file": "Dockerfile",
                "resources": {"limits": {"cpu": 1, "memory": 1024}},
                "build_only": False,
                "depends_on": ["compile"]
            }]
        }

        self.raises_expect(d, "#jobs[0]: Job 'compile' may not depend on itself")

    def test_may_not_create_jobs(self):
        d = {
            "version": 1,
            "jobs": [{
                "type": "docker",
                "name": "Create Jobs",
                "docker_file": "test/Dockerfile_benchmarks",
                "build_only": False,
                "resources": {"limits": {"cpu": 1, "memory": 1024}},
            }]
        }

        self.raises_expect(d, "#jobs[0].name: 'Create Jobs' not a valid value")

    def test_environment(self):
        d = {
            "version": 1,
            "jobs": [{
                "type": "docker",
                "name": "test",
                "docker_file": "Dockerfile",
                "resources": {"limits": {"cpu": 1, "memory": 1024}},
                "environment": None
            }]
        }

        self.raises_expect(d, "#jobs[0].environment: must be an object")

        d['jobs'][0]['environment'] = []
        self.raises_expect(d, "#jobs[0].environment: must be an object")

        d['jobs'][0]['environment'] = {'key': 123}
        self.raises_expect(d, "#jobs[0].environment.key: must be a string or object")

        d['jobs'][0]['environment'] = {'key': {}}
        self.raises_expect(d, "#jobs[0].environment.key: must contain a $secret")

        d['jobs'][0]['environment'] = {'key': {'$secret': None}}
        self.raises_expect(d, "#jobs[0].environment.key.$secret: is not a string")

        d['jobs'][0]['environment'] = {}
        validate_json(d)

    def test_deployments(self):
        d = {
            "version": 1,
            "jobs": [{
                "type": "docker",
                "name": "test",
                "docker_file": "Dockerfile",
                "resources": {"limits": {"cpu": 1, "memory": 1024}},
                "deployments": None
            }]
        }

        self.raises_expect(d, "#jobs[0].deployments: must be an array")

        d['jobs'][0]['deployments'] = []
        self.raises_expect(d, "#jobs[0].deployments: must not be empty")

        d['jobs'][0]['deployments'] = [{}]
        self.raises_expect(d, "#jobs[0].deployments[0]: does not contain a 'type'")

        d['jobs'][0]['deployments'] = [{'type': 'unknown'}]
        self.raises_expect(d, "#jobs[0].deployments[0]: type 'unknown' not supported")

        d['jobs'][0]['deployments'] = [{'type': 'docker-registry', 'host': 'hostname',
                                        'repository': 'repo', 'username': 'user', 'password': 'value'}]
        self.raises_expect(d, "#jobs[0].deployments[0].password: must be an object")

        d['jobs'][0]['deployments'] = [{'type': 'docker-registry', 'host': 'hostname', 'repository': 'repo',
                                        'username': 'user', 'password': {'$secret': 'blub'}}]
        validate_json(d)

    def test_build_arguments(self):
        d = {
            "version": 1,
            "jobs": [{
                "type": "docker",
                "name": "test",
                "docker_file": "Dockerfile",
                "resources": {"limits": {"cpu": 1, "memory": 1024}},
                "build_arguments": None
            }]
        }

        self.raises_expect(d, "#jobs[0].build_arguments: must be an object")

        d['jobs'][0]['build_arguments'] = []
        self.raises_expect(d, "#jobs[0].build_arguments: must be an object")

        d['jobs'][0]['build_arguments'] = {'key': 123}
        self.raises_expect(d, "#jobs[0].build_arguments.key: is not a string")

        d['jobs'][0]['build_arguments'] = {'key': {}}
        self.raises_expect(d, "#jobs[0].build_arguments.key: is not a string")

        d['jobs'][0]['build_arguments'] = {}
        validate_json(d)

    def test_security_context(self):
        d = {
            "version": 1,
            "jobs": [{
                "type": "docker",
                "name": "test",
                "docker_file": "Dockerfile",
                "resources": {"limits": {"cpu": 1, "memory": 1024}},
                "security_context": []
            }]
        }

        self.raises_expect(d, "#jobs[0].security_context: must be an object")

        d['jobs'][0]['security_context'] = {'capabilities': []}
        self.raises_expect(d, "#jobs[0].security_context.capabilities: must be an object")

        d['jobs'][0]['security_context'] = {'capabilities': {'add': {}}}
        self.raises_expect(d, "#jobs[0].security_context.capabilities.add: must be an array")

        d['jobs'][0]['security_context'] = {'capabilities': {'add': [123]}}
        self.raises_expect(d, "#jobs[0].security_context.capabilities.add[0]: is not a string")

        d['jobs'][0]['security_context'] = {'capabilities': {'add': ['CAP']}}
        validate_json(d)

    def test_kubernetes_limits(self):
        d = {
            "version": 1,
            "jobs": [{
                "type": "docker",
                "name": "test",
                "docker_file": "Dockerfile",
                "resources": {
                    "limits": {
                        "cpu": 1, "memory": 1024
                    },
                    "kubernetes": {
                        "limits": {
                            "cpu": 1, "memory": 1024
                        }
                    }
                }
            }]
        }

        validate_json(d)

    def test_valid(self):
        d = {
            "version": 1,
            "jobs": [{
                "type": "docker",
                "name": "compile",
                "docker_file": "test/Dockerfile_benchmarks",
                "build_only": False,
                "resources": {"limits": {"cpu": 1, "memory": 1024}},
            }, {
                "type": "docker",
                "name": "benchmark_server",
                "docker_file": "test/Dockerfile_benchmarks",
                "resources": {"limits": {"cpu": 1, "memory": 1024}},
                "build_only": False,
                "depends_on": ["compile"]
            }, {
                "type": "docker",
                "name": "test_server",
                "docker_file": "test/Dockerfile_test_server",
                "resources": {"limits": {"cpu": 1, "memory": 1024}},
                "build_only": False,
                "depends_on": ["compile"]
            }]
        }

        validate_json(d)
