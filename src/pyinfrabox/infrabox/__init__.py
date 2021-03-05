import re
from builtins import int, range

from pyinfrabox import ValidationError
from pyinfrabox.utils import *

def special_match(strg, search=re.compile(r'[^a-z0-9_-]').search):
    return not bool(search(strg))

def check_name(n, path):
    check_text(n, path)
    if not special_match(n):
        raise ValidationError(path, "'%s' not a valid value" % n)

def parse_repository(d, path):
    check_allowed_properties(d, path, ('clone', 'submodules', 'full_history'))

    if 'clone' in d:
        check_boolean(d['clone'], path + ".clone")

    if 'submodules' in d:
        check_boolean(d['submodules'], path + ".submodules")

    if 'full_history' in d:
        check_boolean(d['full_history'], path + ".full_history")

def parse_cluster(d, path):
    check_allowed_properties(d, path, ('selector',))

    check_string_array(d['selector'], path + ".selector")

def parse_depends_on_condition(d, path):
    check_allowed_properties(d, path, ("job", "on"))
    check_required_properties(d, path, ("job", "on"))
    check_name(d['job'], path + '.job')

    on = d['on']
    if not isinstance(on, list):
        raise ValidationError(path + ".on", "must be a list")

    if not on:
        raise ValidationError(path + ".on", "must not be empty")


    on_used = {}
    for i in on:
        if i not in ('finished', 'error', 'failure', 'unstable', '*'):
            raise ValidationError(path + ".on", "%s is not a valid value" % i)

        if i in on_used:
            raise ValidationError(path + ".on", "%s used twice" % i)

        on_used[i] = True


def parse_depends_on(a, path):
    if not isinstance(a, list):
        raise ValidationError(path, "must be an list")

    if not a:
        raise ValidationError(path, "must not be empty")

    for i in range(0, len(a)):
        n = a[i]
        p = '[%s]' % i

        if isinstance(n, dict):
            # contains conditions
            parse_depends_on_condition(n, path + p)
        else:
            # no conditions, default to 'finished'
            check_name(n, path + p)

def check_version(v, path):
    if not isinstance(v, int):
        raise ValidationError(path, "must be an int")

    if v != 1:
        raise ValidationError(path, "unsupported version")

def parse_build_args(e, path):
    if not isinstance(e, dict):
        raise ValidationError(path, "must be an object")

    for key in e:
        value = e[key]
        p = path + "." + key
        check_text(value, p)

def parse_secret_ref(value, p):
    if not isinstance(value, dict):
        raise ValidationError(p, "must be an object")

    if "$secret" not in value:
        raise ValidationError(p, "must contain a $secret")

    check_text(value['$secret'], p + ".$secret")

def parse_vault_ref(value, p):
    if not isinstance(value, dict):
        raise ValidationError(p, "must be an object")

    if "$vault" not in value:
        raise ValidationError(p, "must contain a $vault")
    check_text(value['$vault'], p + ".$vault")

    if "$vault_secret_path" not in value:
        raise ValidationError(p, "must contain a $vault_secret_path")
    check_text(value['$vault_secret_path'], p + ".$vault_secret_path")

    if "$vault_secret_key" not in value:
        raise ValidationError(p, "must contain a $vault_secret_key")
    check_text(value['$vault_secret_key'], p + ".$vault_secret_key")

def parse_environment(e, path):
    if not isinstance(e, dict):
        raise ValidationError(path, "must be an object")

    for key in e:
        value = e[key]
        p = path + "." + key

        if isinstance(value, dict):
            if '$vault' not in value or '$vault_secret_path' not in value or "$vault_secret_key" not in value:
                parse_secret_ref(value, p)
            else:
                parse_vault_ref(value, p)
        else:
            try:
                check_text(value, p)
            except:
                raise ValidationError(p, "must be a string or object")

def parse_cache(d, path):
    check_allowed_properties(d, path, ("data", "image"))

    if 'data' in d:
        check_boolean(d['data'], path + ".data")

    if 'image' in d:
        check_boolean(d['image'], path + ".image")

def parse_git(d, path):
    check_allowed_properties(d, path, ("type", "name", "commit", "clone_url",
                                       "depends_on", "environment", "infrabox_file", "branch"))
    check_required_properties(d, path, ("type", "name", "commit", "clone_url"))
    check_name(d['name'], path + ".name")
    check_text(d['commit'], path + ".commit")
    check_text(d['clone_url'], path + ".clone_url")

    if 'branch' in d:
        check_text(d['branch'], path + ".clone_url")

    if 'depends_on' in d:
        parse_depends_on(d['depends_on'], path + ".depends_on")

    if 'environment' in d:
        parse_environment(d['environment'], path + ".environment")

    if 'infrabox_file' in d:
        check_text(d['infrabox_file'], path + ".infrabox_file")

def parse_workflow(d, path):
    check_allowed_properties(d, path, ("type", "name", "infrabox_file", "depends_on", "repository"))
    check_required_properties(d, path, ("type", "name", "infrabox_file"))
    check_name(d['name'], path + ".name")
    check_text(d['infrabox_file'], path + ".infrabox_file")

    if 'repository' in d:
        parse_repository(d['repository'], path + ".repository")

    if 'depends_on' in d:
        parse_depends_on(d['depends_on'], path + ".depends_on")

def parse_limits(d, path):
    check_allowed_properties(d, path, ("memory", "cpu"))
    check_required_properties(d, path, ("memory", "cpu"))

    check_int_or_float(d['cpu'], path + ".cpu")
    check_number(d['memory'], path + ".memory")

    if d['cpu'] <= 0.3:
        raise ValidationError(path + ".cpu", "must be greater than 0.3")

    if d['memory'] <= 255:
        raise ValidationError(path + ".memory", "must be greater than 255")

def parse_security_context(d, path):
    check_allowed_properties(d, path, ('privileged',))

    if 'privileged' in d:
        check_boolean(d['privileged'], path + ".privileged")

def parse_services(d, path):
    if not isinstance(d, list):
        raise ValidationError(path, "must be an array")

    names = []

    for i in range(0, len(d)):
        elem = d[i]
        p = "%s[%s]" % (path, i)

        check_allowed_properties(elem, p, ("apiVersion", "kind", "metadata", "spec"))
        check_required_properties(elem, p, ("apiVersion", "kind", "metadata"))
        check_required_properties(elem['metadata'], p + ".metadata", ("name", ))

        name = elem['metadata']['name']

        if name in names:
            raise ValidationError(p, "duplicate service name found: %s" % name)

        names.append(name)

def parse_resources(d, path):
    check_allowed_properties(d, path, ("limits",))
    check_required_properties(d, path, ("limits",))

    parse_limits(d['limits'], path + ".limits")

def parse_docker_image(d, path):
    check_allowed_properties(d, path, ("type", "name", "image", "depends_on", "resources",
                                       "environment", "timeout", "security_context",
                                       "build_context", "cache", "repository", "command",
                                       "deployments", "run",
                                       "cluster", "registries", "services"))
    check_required_properties(d, path, ("type", "name", "image", "resources"))
    check_name(d['name'], path + ".name")
    check_text(d['image'], path + ".image")
    parse_resources(d['resources'], path + ".resources")

    if 'services' in d:
        parse_services(d['services'], path + ".services")

    if 'cluster' in d:
        parse_cluster(d['cluster'], path + ".cluster")

    if 'command' in d:
        check_string_array(d['command'], path + ".command")

    if 'repository' in d:
        parse_repository(d['repository'], path + ".repository")

    if 'cache' in d:
        parse_cache(d['cache'], path + ".cache")

    if 'depends_on' in d:
        parse_depends_on(d['depends_on'], path + ".depends_on")

    if 'environment' in d:
        parse_environment(d['environment'], path + ".environment")

    if 'timeout' in d:
        check_number(d['timeout'], path + ".timeout")

    if 'security_context' in d:
        parse_security_context(d['security_context'], path + '.security_context')

    if 'registries' in d:
        parse_registries(d['registries'], path + '.registries')

    if 'build_context' in d:
        check_text(d['build_context'], path + ".build_context")

    if 'deployments' in d:
        parse_deployments(d['deployments'], path + ".deployments")

    if 'run' in d:
        check_boolean(d['run'], path + ".run")

def parse_docker(d, path):
    check_allowed_properties(d, path, ("type", "name", "docker_file", "depends_on", "resources",
                                       "build_only", "environment", "target",
                                       "build_arguments", "deployments", "timeout", "security_context", "command",
                                       "build_context", "cache", "repository", "cluster", "services", "registries"))
    check_required_properties(d, path, ("type", "name", "docker_file", "resources"))
    check_name(d['name'], path + ".name")
    check_text(d['docker_file'], path + ".docker_file")
    parse_resources(d['resources'], path + ".resources")

    if 'services' in d:
        parse_services(d['services'], path + ".services")

    if 'cluster' in d:
        parse_cluster(d['cluster'], path + ".cluster")

    if 'repository' in d:
        parse_repository(d['repository'], path + ".repository")

    if 'build_only' in d:
        check_boolean(d['build_only'], path + ".build_only")

    if 'cache' in d:
        parse_cache(d['cache'], path + ".cache")

    if 'depends_on' in d:
        parse_depends_on(d['depends_on'], path + ".depends_on")

    if 'environment' in d:
        parse_environment(d['environment'], path + ".environment")

    if 'build_arguments' in d:
        parse_build_args(d['build_arguments'], path + ".build_arguments")

    if 'deployments' in d:
        parse_deployments(d['deployments'], path + ".deployments")

    if 'timeout' in d:
        check_number(d['timeout'], path + ".timeout")

    if 'security_context' in d:
        parse_security_context(d['security_context'], path + '.security_context')

    if 'build_context' in d:
        check_text(d['build_context'], path + ".build_context")

    if 'registries' in d:
        parse_registries(d['registries'], path + '.registries')

    if 'command' in d:
        check_string_array(d['command'], path + ".command")

def parse_docker_compose(d, path):
    check_allowed_properties(d, path, ("type", "name", "docker_compose_file", "depends_on", "stop_timeout",
                                       "environment", "resources", "cache", "timeout", "cluster",
                                       "repository", "registries"))
    check_required_properties(d, path, ("type", "name", "docker_compose_file", "resources"))
    check_name(d['name'], path + ".name")
    check_text(d['docker_compose_file'], path + ".docker_compose_file")
    parse_resources(d['resources'], path + ".resources")

    if 'cluster' in d:
        parse_cluster(d['cluster'], path + ".cluster")

    if 'timeout' in d:
        check_number(d['timeout'], path + ".timeout")

    if 'repository' in d:
        parse_repository(d['repository'], path + ".repository")

    if 'cache' in d:
        parse_cache(d['cache'], path + ".cache")

    if 'depends_on' in d:
        parse_depends_on(d['depends_on'], path + ".depends_on")

    if 'environment' in d:
        parse_environment(d['environment'], path + ".environment")

    if 'registries' in d:
        parse_registries(d['registries'], path + '.registries')

def parse_wait(d, path):
    check_allowed_properties(d, path, ("type", "name", "depends_on"))
    check_required_properties(d, path, ("type", "name"))
    check_name(d['name'], path + ".name")

    if 'depends_on' in d:
        parse_depends_on(d['depends_on'], path + ".depends_on")

def parse_deployment_docker_registry(d, path):
    check_allowed_properties(d, path, ("type", "host", "repository", "username", "password", "tag", "target", "always_push"))
    check_required_properties(d, path, ("type", "host", "repository"))
    check_text(d['host'], path + ".host")
    check_text(d['repository'], path + ".repository")

    if 'username' in d:
        check_text(d['username'], path + ".username")

    if 'tag' in d:
        check_text(d['tag'], path + ".tag")

    if 'target' in d:
        check_text(d['target'], path + ".target")

    if 'password' in d:
        parse_secret_ref(d['password'], path + ".password")

def parse_registry_docker_registry(d, path):
    check_required_properties(d, path, ("type", "host", "repository", "username", "password"))
    check_text(d['host'], path + ".host")
    check_text(d['repository'], path + ".repository")
    check_text(d['username'], path + ".username")
    parse_secret_ref(d['password'], path + ".password")

def parse_registry_ecr(d, path):
    check_required_properties(d, path, ("type", "access_key_id", "secret_access_key", "region", "host"))

    check_text(d['host'], path + ".host")
    check_text(d['region'], path + ".region")
    parse_secret_ref(d['secret_access_key'], path + ".secret_access_key")
    parse_secret_ref(d['access_key_id'], path + ".access_key_id")

def parse_deployment_ecr(d, path):
    check_allowed_properties(d, path, ("type", "access_key_id", "secret_access_key",
                                       "region", "repository", "host", "tag", "target"))
    check_required_properties(d, path, ("type", "access_key_id", "secret_access_key", "region", "repository", "host"))

    check_text(d['host'], path + ".host")
    check_text(d['repository'], path + ".repository")
    check_text(d['region'], path + ".region")
    parse_secret_ref(d['secret_access_key'], path + ".secret_access_key")
    parse_secret_ref(d['access_key_id'], path + ".access_key_id")

    if 'tag' in d:
        check_text(d['tag'], path + ".tag")

    if 'target' in d:
        check_text(d['target'], path + ".target")

def parse_registry_gcr(d, path):
    check_required_properties(d, path, ("type", "service_account", "repository", "host"))
    parse_secret_ref(d['service_account'], path + ".service_account")

    check_text(d['host'], path + ".host")
    check_text(d['repository'], path + ".region")
    parse_secret_ref(d['service_account'], path + ".service_account")

def parse_deployment_gcr(d, path):
    check_allowed_properties(d, path, ("type", "service_account", "repository", "host", "tag", "target"))
    check_required_properties(d, path, ("type", "service_account", "repository", "host"))

    check_text(d['host'], path + ".host")
    check_text(d['repository'], path + ".repository")

    parse_secret_ref(d['service_account'], path + ".service_account")

    if 'tag' in d:
        check_text(d['tag'], path + ".tag")

    if 'target' in d:
        check_text(d['target'], path + ".target")

def parse_registries(e, path):
    if not isinstance(e, list):
        raise ValidationError(path, "must be an array")

    if not e:
        raise ValidationError(path, "must not be empty")

    for i in range(0, len(e)):
        elem = e[i]
        p = "%s[%s]" % (path, i)

        if 'type' not in elem:
            raise ValidationError(p, "does not contain a 'type'")

        t = elem['type']

        if t == 'docker-registry':
            parse_registry_docker_registry(elem, p)
        elif t == 'ecr':
            parse_registry_ecr(elem, p)
        elif t == 'gcr':
            parse_registry_gcr(elem, p)
        else:
            raise ValidationError(p, "type '%s' not supported" % t)


def parse_deployments(e, path):
    if not isinstance(e, list):
        raise ValidationError(path, "must be an array")

    if not e:
        raise ValidationError(path, "must not be empty")

    for i in range(0, len(e)):
        elem = e[i]
        p = "%s[%s]" % (path, i)

        if 'type' not in elem:
            raise ValidationError(p, "does not contain a 'type'")

        t = elem['type']

        if t == 'docker-registry':
            parse_deployment_docker_registry(elem, p)
        elif t == 'ecr':
            parse_deployment_ecr(elem, p)
        elif t == 'gcr':
            parse_deployment_gcr(elem, p)
        else:
            raise ValidationError(p, "type '%s' not supported" % t)


def parse_jobs(e, path):
    if not isinstance(e, list):
        raise ValidationError(path, "must be an array")

    for i in range(0, len(e)):
        elem = e[i]
        p = "%s[%s]" % (path, i)

        if 'type' not in elem:
            raise ValidationError(p, "does not contain a 'type'")

        t = elem['type']

        if t == 'git':
            parse_git(elem, p)
        elif t == 'wait':
            parse_wait(elem, p)
        elif t == 'workflow':
            parse_workflow(elem, p)
        elif t == 'docker':
            parse_docker(elem, p)
        elif t == 'docker-image':
            parse_docker_image(elem, p)
        elif t == 'docker-compose':
            parse_docker_compose(elem, p)
        else:
            raise ValidationError(p, "type '%s' not supported" % t)

def parse_document(d):
    check_allowed_properties(d, "#", ("version", "jobs"))
    check_required_properties(d, "#", ("version", "jobs"))

    check_version(d['version'], "#version")

    if 'jobs' in d:
        parse_jobs(d['jobs'], "#jobs")

def validate_json(d):
    parse_document(d)

    if 'jobs' not in d:
        return True

    jobs = {}
    all_job_names = set([j['name'] for j in d['jobs']])
    all_deps = {}
    for i in range(0, len(d['jobs'])):
        job = d['jobs'][i]
        job_name = job['name']

        path = "#jobs[%s]" % i

        if jobs.get(job_name, None):
            raise ValidationError(path + ".name", "Job name '%s' already exists" % job_name)

        if job_name == 'Create Jobs':
            raise ValidationError(path + ".name", "Job name may not be 'Create Jobs'")

        jobs[job_name] = job

        if 'depends_on' not in job:
            continue

        deps = {}
        for depends_on in job['depends_on']:
            parent_name = None

            if isinstance(depends_on, dict):
                parent_name = depends_on['job']
            else:
                parent_name = depends_on

            if job_name == parent_name:
                raise ValidationError(path, "Job '%s' may not depend on itself" % parent_name)

            if parent_name not in all_job_names:
                raise ValidationError(path + ".depends_on", "Job '%s' not found" % parent_name)

            if parent_name in deps:
                raise ValidationError(path + ".depends_on", "'%s' duplicate dependencies" % parent_name)

            deps[parent_name] = True

        if deps:
            all_deps[job_name] = deps

    for job_name, deps in all_deps.items():
        queue = list(deps.keys())
        for dep_job in queue:
            if dep_job == job_name:
                raise ValidationError("Jobs", "Circular dependency detected.")
            if dep_job in all_deps:
                queue.extend(all_deps[dep_job].keys())

    return True
