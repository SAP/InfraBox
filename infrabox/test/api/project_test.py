from temp_tools import TestClient
from test_template import ApiTestTemplate
from pyinfraboxutils.storage import storage
from os import getcwd, stat

class ProjectTest(ApiTestTemplate):

    url_ns = 'api/v1/projects'

    def test_get_project_does_not_exist(self):
        r = TestClient.get('/api/v1/projects/%s' % self.repo_id, TestClient.get_user_authorization(self.user_id))
        self.assertEqual(r['message'], 'Unauthorized')

    def test_get_project(self):
        r = TestClient.get('/api/v1/projects/%s' % self.project_id, TestClient.get_user_authorization(self.user_id))
        self.assertEqual(r['id'], self.project_id)
