from temp_tools import TestClient
from test_template import ApiTestTemplate


class UserTest(ApiTestTemplate):

    def test_get_users(self):

        # test no user
        r = TestClient.get('/api/v1/user', TestClient.get_job_authorization(self.job_id))
        self.assertEqual(r['message'], 'Unauthorized')
        #self.assertEqual(r['status'], 404)

        # test user data
        r = TestClient.get('/api/v1/user', TestClient.get_user_authorization(self.user_id))
        self.assertEqual(r['username'], self.author_name)
        self.assertEqual(r['github_id'], self.user_github_id)
