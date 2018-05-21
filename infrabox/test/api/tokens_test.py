from temp_tools import TestClient
from test_template import ApiTestTemplate

class TokensTest(ApiTestTemplate):

    def setUp(self):
        super(TokensTest, self).setUp()
        TestClient.execute("""TRUNCATE auth_token""")
        self.test_token_data = {'description': 'Test token 1',
                                'scope_push': True,
                                'scope_pull': True}

    def test_tokens_root(self):

        # test unauthorized
        r = TestClient.post('api/v1/projects/%s/tokens' % self.project_id, data=self.test_token_data,
                            headers=TestClient.get_job_authorization(self.job_id))
        self.assertEqual(r['message'], 'Unauthorized')

        # test token creation
        r = TestClient.post('api/v1/projects/%s/tokens' % self.project_id, data=self.test_token_data,
                            headers=TestClient.get_user_authorization(self.user_id))
        self.assertEqual(r['message'], 'Successfully added token.')
        self.assertEqual(r['status'], 200)

        # test token receiving
        r = TestClient.get('api/v1/projects/%s/tokens' % self.project_id,
                            headers=TestClient.get_user_authorization(self.user_id))

        self.assertGreater(len(r), 0)
        self.assertEqual(r[0]['description'], self.test_token_data['description'])
        self.assertEqual(r[0]['scope_push'], self.test_token_data['scope_push'])
        self.assertEqual(r[0]['scope_pull'], self.test_token_data['scope_pull'])

    def test_tokens_delete(self):

        r = TestClient.execute_one('''
            INSERT INTO auth_token (description, scope_push, scope_pull, project_id)
            VALUES (%s, %s, %s, %s) RETURNING id
        ''', [self.test_token_data['description'], self.test_token_data['scope_push'],
              self.test_token_data['scope_pull'], self.project_id])
        token_id = r['id']

        r = TestClient.execute_one("""SELECT count(*) FROM auth_token WHERE id = '%s'""" % token_id)
        self.assertGreater(r[0], 0)

        r = TestClient.delete('api/v1/projects/%s/tokens/%s' % (self.project_id, token_id),
                              headers=TestClient.get_user_authorization(self.user_id))

        self.assertEqual(r['message'], 'Successfully deleted token.')
        self.assertEqual(r['status'], 200)

        r = TestClient.execute_one("""SELECT count(*) FROM auth_token WHERE id = '%s'""" % token_id)
        self.assertEqual(r[0], 0)
