import time
import json

import urllib3
import requests
import cachetclient.cachet as cachet

from pyinfraboxutils import get_env, get_logger
from pyinfraboxutils.db import DB, connect_db

try:
    from functools import partialmethod
except ImportError:
    # Python 2 fallback: https://gist.github.com/carymrobbins/8940382
    from functools import partial

    class partialmethod(partial):
        def __get__(self, instance, owner):
            if instance is None:
                return self

            return partial(self.func, instance, *(self.args or ()), **(self.keywords or {}))

# TODO: Support custom ca bundles
session = requests.Session
old_request = session.request
session.request = partialmethod(old_request, verify=False)

urllib3.disable_warnings()

logger = get_logger('state')

class Cachet(object):
    def __init__(self):
        self.endpoint = get_env('INFRABOX_CACHET_ENDPOINT')
        self.api_token = get_env('INFRABOX_CACHET_API_TOKEN')
        self.components = {}
        self.metrics = {}

    def _create(self, db):
        # Create Group
        groups = cachet.Groups(endpoint=self.endpoint, api_token=self.api_token)
        group_list = json.loads(groups.get(name='Clusters'))

        gid = None
        if not group_list['data']:
            group = json.loads(groups.post(name='Clusters'))
            gid = group['data']['id']
        else:
            gid = group_list['data'][0]['id']

        # Create Components
        components = cachet.Components(endpoint=self.endpoint, api_token=self.api_token)
        clusters = db.execute_many_dict("""
            SELECT name
            FROM cluster
        """)

        for i, c in enumerate(clusters):
            if c['name'] in self.components:
                continue

            cid = self._get_component_id(c['name'])
            if not cid:
                a = components.post(name=c['name'],
                                    description=c['name'],
                                    status=1,
                                    order=i,
                                    group_id=gid,
                                    enabled=True)
                component = json.loads(a)
                cid = component['data']['id']

            self.components[c['name']] = cid

        # Create metrics
        mid = self._get_metric_id('Running Jobs')

        if not mid:
            metrics = cachet.Metrics(endpoint=self.endpoint, api_token=self.api_token)
            m = metrics.post(name='Running Jobs',
                             suffix='jobs',
                             description='Currently active jobs',
                             default_value=0,
                             places=0,
                             calc_type=1)
            mid = json.loads(m)['data']['id']

        self.metrics['Running Jobs'] = mid

    def _get_component_id(self, name):
        components = cachet.Components(endpoint=self.endpoint, api_token=self.api_token)
        data = json.loads(components.get())

        for c in data['data']:
            if c['name'] == name:
                return c['id']

        return None

    def _get_metric_id(self, name):
        metrics = cachet.Metrics(endpoint=self.endpoint, api_token=self.api_token)
        data = json.loads(metrics.get())

        for c in data['data']:
            if c['name'] == name:
                return c['id']

        return None

    def update(self, db):
        self._create(db)

        clusters = db.execute_many_dict("""
            SELECT name, active, enabled
            FROM cluster
        """)

        for c in clusters:
            cid = self.components[c['name']]

            status = 1
            if not c['active'] or not c['enabled']:
                status = 4

            components = cachet.Components(endpoint=self.endpoint,
                                           api_token=self.api_token)
            components.put(id=cid, status=status, enabled=True)

        jobs = db.execute_one_dict("""
            SELECT count(*) as count
            FROM job
            WHERE state = 'running'
        """)

        mid = self.metrics['Running Jobs']
        points = cachet.Points(endpoint=self.endpoint, api_token=self.api_token)

        logger.info('Running jobs: %s', jobs['count'])
        points.post(id=mid, value=jobs['count'], timestamp=int(time.time()))

def main(): # pragma: no cover
    get_env('INFRABOX_DATABASE_HOST')
    get_env('INFRABOX_DATABASE_USER')
    get_env('INFRABOX_DATABASE_PASSWORD')
    get_env('INFRABOX_DATABASE_PORT')
    get_env('INFRABOX_DATABASE_DB')
    get_env('INFRABOX_CACHET_ENDPOINT')
    get_env('INFRABOX_CACHET_API_TOKEN')

    while True:
        c = Cachet()
        try:
            db = DB(connect_db())
            c.update(db)
        except Exception as e:
            logger.exception(e)
        finally:
            time.sleep(10)

if __name__ == "__main__": # pragma: no cover
    main()
