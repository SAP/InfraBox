import yaml

def handle_version(d, r):
    if str(d['version']) != "2":
        raise Exception("version '%s' not supported" % d['version'])

    r["version"] = "2"

def handle_service(name, d, r):
    r['services'][name] = {
        "dns": "8.8.8.8",
        "dns_search": ""
    }

    for key, value in d[name].iteritems():
        if key == "links":
            r['services'][name]['links'] = value
        elif key == "environment":
            r['services'][name]['environment'] = value
        elif key == "build":
            r['services'][name]['build'] = value
        elif key == "command":
            r['services'][name]['command'] = value
        elif key == "image":
            r['services'][name]['image'] = value
        elif key == "container_name":
            r['services'][name]['container_name'] = value
        elif key == "depends_on":
            r['services'][name]['depends_on'] = value
        elif key == "entrypoiny":
            r['services'][name]['entrypoint'] = value
        elif key == "links":
            r['services'][name]['links'] = value
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
        else:
            raise Exception("[%s] not supported" % key)

    return r

def create_from(path):
    with open(path) as f:
        d = yaml.load(f.read())
        return parse(d)
