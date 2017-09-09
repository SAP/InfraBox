from nose.tools import eq_, assert_raises

from pyinfrabox import ValidationError
from pyinfrabox.infrabox import validate_json

def raises_expect(data, expected):
    with assert_raises(ValidationError) as e:
        validate_json(data)

    eq_(e.exception.message, expected)

def test_version():
    raises_expect({}, "#: property 'version' is required")
    raises_expect({'version': 'asd', 'jobs': []}, "#version: must be an int")
    raises_expect({'version': '1', 'jobs': []}, "#version: must be an int")
    raises_expect({'version': 2, 'jobs': []}, "#version: unsupported version")

def test_jobs():
    raises_expect({'version': 1}, "#: Either 'jobs' or 'generator' must be set")
    raises_expect({'version': 1, 'jobs': 'asd'}, "#jobs: must be an array")
    raises_expect({'version': 1, 'jobs': []}, "#jobs: must not be empty")
    raises_expect({'version': 1, 'jobs': [{}]}, "#jobs[0]: does not contain a 'type'")

def test_dep_defined_later():
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

    raises_expect(d, "#jobs[0].depends_on: Job 'compile' not found")

def test_dep_not_found():
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

    raises_expect(d, "#jobs[0].depends_on: Job 'not_found' not found")

def test_deps_must_be_unique():
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

    raises_expect(d, "#jobs[1].depends_on: 'source' duplicate dependencies")

def test_duplicate_job_name():
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

    raises_expect(d, "#jobs[1].name: Job name 'compile' already exists")

def test_dependency_conditions():
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

    raises_expect(d, "#jobs[1].depends_on[0].on: must be a list")

    d['jobs'][1]['depends_on'] = [{"job": "compile", "on": []}]
    raises_expect(d, "#jobs[1].depends_on[0].on: must not be empty")

    d['jobs'][1]['depends_on'] = [{"job": "compile", "on": [True]}]
    raises_expect(d, "#jobs[1].depends_on[0].on: True is not a valid value")

    d['jobs'][1]['depends_on'] = [{"job": "compile", "on": ["not valid"]}]
    raises_expect(d, "#jobs[1].depends_on[0].on: not valid is not a valid value")

    d['jobs'][1]['depends_on'] = [{"job": "not-valid", "on": ["*"]}]
    raises_expect(d, "#jobs[1].depends_on: Job 'not-valid' not found")

    d['jobs'][1]['depends_on'] = [{"job": "compile", "on": ["error", "error"]}]
    raises_expect(d, "#jobs[1].depends_on[0].on: error used twice")


def test_empty_dep_array():
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

    raises_expect(d, "#jobs[0].depends_on: must not be empty")

def test_invalid_name():
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

    raises_expect(d, "#jobs[0].name: '../blub' not a valid value")

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

    raises_expect(d, "#jobs[0].name: 'blub\'' not a valid value")

def test_may_not_depend_on_itself():
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

    raises_expect(d, "#jobs[0]: Job 'compile' may not depend on itself")

def test_may_not_create_jobs():
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

    raises_expect(d, "#jobs[0].name: 'Create Jobs' not a valid value")

def test_environment():
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

    raises_expect(d, "#jobs[0].environment: must be an object")

    d['jobs'][0]['environment'] = []
    raises_expect(d, "#jobs[0].environment: must be an object")

    d['jobs'][0]['environment'] = {'key': 123}
    raises_expect(d, "#jobs[0].environment.key: must be a string or object")

    d['jobs'][0]['environment'] = {'key': {}}
    raises_expect(d, "#jobs[0].environment.key: must contain a $ref")

    d['jobs'][0]['environment'] = {'key': {'$ref': None}}
    raises_expect(d, "#jobs[0].environment.key.$ref: is not a string")

    d['jobs'][0]['environment'] = {}
    validate_json(d)

def test_deployments():
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

    raises_expect(d, "#jobs[0].deployments: must be an array")

    d['jobs'][0]['deployments'] = []
    raises_expect(d, "#jobs[0].deployments: must not be empty")

    d['jobs'][0]['deployments'] = [{}]
    raises_expect(d, "#jobs[0].deployments[0]: does not contain a 'type'")

    d['jobs'][0]['deployments'] = [{'type': 'unknown'}]
    raises_expect(d, "#jobs[0].deployments[0]: type 'unknown' not supported")

    d['jobs'][0]['deployments'] = [{'type': 'docker-registry', 'host': 'hostname', 'repository': 'repo', 'username': 'user', 'password': 'value'}]
    raises_expect(d, "#jobs[0].deployments[0].password: must be an object")

    d['jobs'][0]['deployments'] = [{'type': 'docker-registry', 'host': 'hostname', 'repository': 'repo', 'username': 'user', 'password': {'$ref': 'blub'}}]
    validate_json(d)

def test_build_arguments():
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

    raises_expect(d, "#jobs[0].build_arguments: must be an object")

    d['jobs'][0]['build_arguments'] = []
    raises_expect(d, "#jobs[0].build_arguments: must be an object")

    d['jobs'][0]['build_arguments'] = {'key': 123}
    raises_expect(d, "#jobs[0].build_arguments.key: is not a string")

    d['jobs'][0]['build_arguments'] = {'key': {}}
    raises_expect(d, "#jobs[0].build_arguments.key: is not a string")

    d['jobs'][0]['build_arguments'] = {}
    validate_json(d)

def test_valid():
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
