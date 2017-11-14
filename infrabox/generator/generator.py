import shutil
import json
import os

def main():
    shutil.copyfile('/generator/infrabox.json', '/infrabox/output/infrabox.json')
    shutil.copyfile('/generator/tests.json', '/infrabox/output/tests.json')

    deployments = None
    with open('/generator/deployments.json') as dep:
        deployments = json.load(dep)

    tag = os.environ.get('INFRABOX_GIT_TAG', None)
    if tag:
        for j in deployments['jobs']:
            for d in j['deployments']:
                d['tag'] = tag

    with open('/infrabox/output/deployments.json', 'w') as out:
        json.dump(deployments, out)

if __name__ == "__main__":
    main()
