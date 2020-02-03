import json
from os import getcwd

from temp_tools import TestClient
from test_template import ApiTestTemplate


class ProjectTest(ApiTestTemplate):

    url_ns = 'api/v1/projects'

    def test_get_project_does_not_exist(self):
        r = TestClient.get('/api/v1/projects/%s' % self.repo_id, TestClient.get_user_authorization(self.user_id))
        self.assertEqual(r['message'], 'Unauthorized')

    def test_get_project(self):
        r = TestClient.get('/api/v1/projects/%s' % self.project_id, TestClient.get_user_authorization(self.user_id))
        self.assertEqual(r['id'], self.project_id)

    def test_get_archive_missing_required_argument(self):
        r = TestClient.get('/api/v1/projects/%s/archive?filename=foo' % self.project_id, TestClient.get_user_authorization(self.user_id))
        self.assertIn('was not found on the server', r['message'])

    def test_get_archive_missing_permissions(self):
        r = TestClient.get('/api/v1/projects/%s/archive?filename=foo' % self.project_id_no_collab, TestClient.get_user_authorization(self.user_id))
        self.assertIn('Unauthorized', r['message'])

    def test_get_archive_does_not_exist(self):
        r = TestClient.get('/api/v1/projects/%s/archive?filename=foo&job_name=bar' % self.project_id, TestClient.get_user_authorization(self.user_id))
        self.assertIn('was not found on the server', r['message'])

    def test_get_archive(self):
        filename = 'test.json'
        file_path = getcwd() + '/' + filename
        test_content = {'foo':'bar'}
        with open(file_path, 'w+') as test_data:
            json.dump({'foo':'bar'}, test_data)
            test_data.flush()
            test_data.seek(0)
            files = {filename: test_data}
            r = TestClient.post('/api/job/archive', data=files, headers=TestClient.get_job_authorization(self.job_id_running),
                                content_type='multipart/form-data')
            self.assertEqual(r.get('message'), 'File uploaded')
        # upload project
        r = TestClient.get('/api/v1/projects/%s/archive?filename=test.json&job_name=running_job' % self.project_id, TestClient.get_user_authorization(self.user_id))
        self.assertEqual(test_content, json.loads(r.data))
        r = TestClient.get('/api/v1/projects/%s/archive?filename=test.json&job_name=running_job&branch=foo' % self.project_id, TestClient.get_user_authorization(self.user_id))
        self.assertEqual(test_content, json.loads(r.data))

        # github project
        TestClient.execute("""
            UPDATE project SET type='github' WHERE id=%s
        """, [self.project_id])
        r = TestClient.get('/api/v1/projects/%s/archive?filename=test.json&job_name=running_job&branch=foo' % self.project_id, TestClient.get_user_authorization(self.user_id))
        self.assertIn('was not found on the server', r['message'])
        r = TestClient.get('/api/v1/projects/%s/archive?filename=test.json&job_name=running_job&branch=branch1' % self.project_id, TestClient.get_user_authorization(self.user_id))
        self.assertEqual(test_content, json.loads(r.data))

    def test_get_archive_for_branch(self):
        pass