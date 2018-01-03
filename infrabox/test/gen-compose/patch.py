import copy
import os
import yaml

data = None
with open('/infrabox/output/e2e/compose/docker-compose.yml') as i:
    data = yaml.load(i)

#del data['services']['api']['image']
#data['services']['api']['build'] = {
#    'context': '../../../../..',
#    'dockerfile': 'src/api-new/Dockerfile'
#}

env = None
if os.environ.get('INFRABOX_CLI', None):
    env = ['INFRABOX_DOCKER_COMPOSE_PROJECT_PREFIX=infrabox']
else:
    env = ['INFRABOX_DOCKER_COMPOSE_PROJECT_PREFIX=compose']

data['services']['scheduler']['environment'] += env

data['services']['test'] = {
    'build': {
        'context': '../../../../..',
        'dockerfile': 'infrabox/test/e2e-compose/Dockerfile'
    },
    'environment': [
        'INFRABOX_DATABASE_HOST=postgres',
        'INFRABOX_DATABASE_DB=postgres',
        'INFRABOX_DATABASE_USER=postgres',
        'INFRABOX_DATABASE_PORT=5432',
        'INFRABOX_DATABASE_PASSWORD=postgres',
        'INFRABOX_API_URL=http://nginx-ingress/api'
    ],
    'links': ['postgres', 'nginx-ingress'],
    'networks': ['infrabox'],
    'volumes': copy.deepcopy(data['services']['dashboard-api']['volumes'])
}

with open('/infrabox/output/e2e/compose/docker-compose.yml', 'w') as o:
    yaml.dump(data, o, default_flow_style=False)
