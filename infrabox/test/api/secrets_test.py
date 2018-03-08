from temp_tools import TestClient
from test_template import ApiTestTemplate

class SekretsTest(ApiTestTemplate):



    def setUp(self):
        super(SekretsTest, self).setUp()
        self.test_secret_data = {'name': 'Test secret 1',
                                 'value': 'JFPOIEHEBLJSFUGFSUYDWGFSDBUWFGDSLKFGWYFGSDJ'}

    def test_secrets_root(self):

        # test unauthorized
        r = TestClient.post('api/v1/projects/%s/secrets' % self.project_id, data=self.test_secret_data,
                            headers=TestClient.get_job_authorization(self.job_id))
        self.assertEqual(r['message'], 'Unauthorized')

        # test token creation
        r = TestClient.post('api/v1/projects/%s/secrets/' % self.project_id, data=self.test_secret_data,
                            headers=TestClient.get_user_authorization(self.user_id))
        self.assertEqual(r['message'], 'Successfully added secret')
        self.assertEqual(r['status'], 200)

        # test token receiving
        r = TestClient.get('api/v1/projects/%s/secrets' % self.project_id,
                            headers=TestClient.get_user_authorization(self.user_id))

        self.assertGreater(len(r), 0)
        self.assertEqual(r[0]['name'], self.test_secret_data['name'])

    def test_secret_delete(self):

        r = TestClient.execute_one('''
            INSERT INTO secret (project_id, name, value)
            VALUES (%s, %s, %s) RETURNING id
        ''', [self.project_id, self.test_secret_data['name'], self.test_secret_data['value']])
        secret_id = r['id']

        r = TestClient.execute_one("""SELECT count(*) FROM secret WHERE id = %s""", [secret_id])
        self.assertGreater(r[0], 0)

        r = TestClient.delete('api/v1/projects/%s/secrets/%s' % (self.project_id, secret_id),
                              headers=TestClient.get_user_authorization(self.user_id))

        self.assertEqual(r['message'], 'Successfully deleted secret')
        self.assertEqual(r['status'], 200)

        r = TestClient.execute_one("""SELECT count(*) FROM secret WHERE id = %s""", [secret_id])
        self.assertEqual(r[0], 0)
