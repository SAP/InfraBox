import shutil
import json
import os
import copy

def main():
    shutil.copyfile('/generator/infrabox.json', '/infrabox/output/infrabox.json')
    shutil.copyfile('/generator/tests.json', '/infrabox/output/tests.json')

    deployments = None
    with open('/generator/deployments.json') as dep:
        deployments = json.load(dep)

    tag = os.environ.get('INFRABOX_GIT_TAG', None)
    if tag:
        for j in deployments['jobs']:
            deps = j.get('deployments', [])

            if not deps:
                continue

            new_deps = []

            for d in deps:
                new_dep_tag = copy.deepcopy(d)
                new_dep_latest = copy.deepcopy(d)

                new_dep_tag['tag'] = tag
                new_dep_latest['tag'] = 'latest'

                new_deps.append(d)
                new_deps.append(new_dep_tag)
                new_deps.append(new_dep_latest)

            j['deployments'] = new_deps

    branch = os.environ.get('INFRABOX_BRANCH', None)
    if not branch:
        for j in deployments['jobs']:
            if 'deployments' in j:
                del j['deployments']


    with open('/infrabox/output/deployments.json', 'w') as out:
        print json.dumps(deployments, indent=4)
        json.dump(deployments, out)

if __name__ == "__main__":
    main()
