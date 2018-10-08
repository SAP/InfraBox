import unittest
from os import getcwd, stat

from pyinfraboxutils.token import encode_job_token
from temp_tools import TestClient
from test_template import ApiTestTemplate

class BuildTest(ApiTestTemplate):

    url_ns = 'api/v1/projects/%s/builds'

    def test_builds_list(self):
        respond = TestClient.get('api/v1/projects/%s/builds/' % self.project_id,
                                 TestClient.get_project_authorization(self.token_id, self.project_id))
        self.assertGreater(len(respond), 0)
        self.assertEqual(respond[0]['id'], self.build_id)

    def test_build(self):
        respond = TestClient.get('api/v1/projects/%s/builds/%s' % (self.project_id, self.build_id),
                                 TestClient.get_project_authorization(self.token_id, self.project_id))
        self.assertEqual(respond[0]['id'], self.build_id)

    def test_build_jobs(self):
        respond = TestClient.get('api/v1/projects/%s/builds/%s/jobs' % (self.project_id, self.build_id),
                                 TestClient.get_project_authorization(self.token_id, self.project_id))
        self.assertGreater(len(respond), 0)



