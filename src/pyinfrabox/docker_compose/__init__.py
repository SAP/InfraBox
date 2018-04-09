import yaml

def handle_version(d, r):
    supported_versions = ("3.2",)
    v = str(d['version'])
    if v not in supported_versions:
        raise Exception("version not supported, supported version is 3.2")

    r["version"] = v

def handle_service(name, d, r):
    r['services'][name] = {}

    for key, value in d[name].items():
        allowed_fields = [
            'links',
            'environment',
            'networks',
            'tty',
            'volumes',
            'ports',
            'restart',
            'build',
            'command',
            'image',
            'container_name',
            'depends_on',
            'entrypoint',
            'links'
        ]

        if key in allowed_fields:
            r['services'][name][key] = value
        else:
            raise Exception("[services][%s][%s] not supported" % (name, key))

def handle_services(d, r):
    d = d['services']
    r['services'] = {}
    for key in d.keys():
        handle_service(key, d, r)


def parse(d):
    r = {}

    if not d:
        raise Exception("invalid file")

    if "version" not in d:
        raise Exception("version not found")

    if "services" not in d:
        raise Exception("services not found")

    for key in d.keys():
        if key == "version":
            handle_version(d, r)
        elif key == "services":
            handle_services(d, r)
        elif key == "networks":
            r[key] = d[key]
        else:
            raise Exception("[%s] not supported" % key)

    return r

def create_from(path):
    with open(path) as f:
        d = yaml.load(f.read())
        return parse(d)
