from os import stat, remove

import json

from temp_tools import TestClient
from test_template import ApiTestTemplate

class JobTest(ApiTestTemplate):

    def test_get_job(self):
        r = TestClient.get('/api/v1/projects/%s/jobs/%s' % (self.project_id, self.job_id),
                           TestClient.get_project_authorization(self.token_id, self.project_id))
        self.assertEqual(r['id'], self.job_id)

    def test_get_job_manifest(self):
        r = TestClient.get('/api/v1/projects/%s/jobs/%s/manifest' % (self.project_id, self.job_id),
                           TestClient.get_project_authorization(self.token_id, self.project_id))
        self.assertEqual(r['id'], self.job_id)
