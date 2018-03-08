from temp_tools import TestClient
from test_template import ApiTestTemplate


class CollaboratorsTest(ApiTestTemplate):

    def setUp(self):
        super(CollaboratorsTest, self).setUp()
        self.test_collaborator_data = {'name': 'collaborator name1'}
        self.collaborator_id = '5432af82-3c4f-4bb5-b1da-a33a0ced0e6f'

    def test_collaborators_root(self):

        TestClient.execute("""
                       INSERT INTO "user" (id, github_id, username,
                           avatar_url)
                       VALUES (%s, 2, %s, 'url1');
                   """, [self.collaborator_id, self.test_collaborator_data['name']])

        # test collaborator creation
        r = TestClient.post('api/v1/projects/%s/collaborators' % self.project_id, data=self.test_collaborator_data,
                            headers=TestClient.get_user_authorization(self.user_id))
        self.assertEqual(r['message'], 'Successfully added user')
        self.assertEqual(r['status'], 200)

        # test unauthorized
        r = TestClient.get('api/v1/projects/%s/collaborators' % self.project_id,
                           headers=TestClient.get_job_authorization(self.job_id))
        self.assertEqual(r['message'], 'Unauthorized')

        # test receiving collaborators list
        r = TestClient.get('api/v1/projects/%s/collaborators' % self.project_id,
                            headers=TestClient.get_user_authorization(self.user_id))

        self.assertGreater(len(r), 0)

        self.assertTrue(any(d['username'] == self.test_collaborator_data['name'] for d in r))
        self.assertTrue(any(d['id'] == self.collaborator_id for d in r))


    def test_collaborators_delete(self):
        TestClient.execute('''
            INSERT INTO collaborator (user_id, project_id, owner)
            VALUES (%s, %s, false)
        ''', [self.collaborator_id, self.project_id])

        # make sure collaborator insert succeed
        r = TestClient.execute_one("""SELECT count(*) FROM collaborator WHERE user_id = %s""",
                                   [self.collaborator_id])
        self.assertGreater(r[0], 0)

        # removing collaborator
        r = TestClient.delete('api/v1/projects/%s/collaborators/%s'
                              % (self.project_id, self.collaborator_id),
                              headers=TestClient.get_user_authorization(self.user_id))

        self.assertEqual(r['message'], 'Successfully removed user')
        self.assertEqual(r['status'], 200)

        # check database not contain this collaborator
        r = TestClient.execute_one("""SELECT count(*) FROM collaborator WHERE user_id = %s""",
                                   [self.collaborator_id])
        self.assertEqual(r[0], 0)
