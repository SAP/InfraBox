import json

from temp_tools import TestClient
from test_template import ApiTestTemplate


class CollaboratorsTest(ApiTestTemplate):

    def setUp(self):
        super(CollaboratorsTest, self).setUp()
        self.test_collaborator_data = {'username': 'collaborator name1', 'role': 'Developer'}
        self.collaborator_id = '5432af82-3c4f-4bb5-b1da-a33a0ced0e6f'

    def test_collaborators_root(self):
        TestClient.execute("""
                           INSERT INTO "user" (id, github_id, username, avatar_url)
                           VALUES (%s, 2, %s, 'url1');
                           """, [self.collaborator_id,
                                 self.test_collaborator_data['username']])

        # test collaborator's creation
        r = TestClient.post('api/v1/projects/%s/collaborators' % self.project_id,
                            data=self.test_collaborator_data,
                            headers=TestClient.get_user_authorization(self.user_id))
        self.assertEqual(r['message'], 'Successfully added user.')
        self.assertEqual(r['status'], 200)

        # test unauthorized
        r = TestClient.get('api/v1/projects/%s/collaborators' % self.project_id,
                           headers=TestClient.get_job_authorization(self.job_id))
        self.assertEqual(r['message'], 'Unauthorized')

        # test receiving collaborators list
        r = TestClient.get('api/v1/projects/%s/collaborators' % self.project_id,
                           headers=TestClient.get_user_authorization(self.user_id))

        self.assertGreater(len(r), 0)

        self.assertTrue(any(d['username'] == self.test_collaborator_data['username'] for d in r))
        self.assertTrue(any(d['id'] == self.collaborator_id for d in r))

    def test_collaborators_delete(self):
        TestClient.execute("""
                           INSERT INTO collaborator (user_id, project_id, role)
                           VALUES (%s, %s, 'Developer')
                           """, [self.collaborator_id, self.project_id])

        TestClient.opa_push()

        # make sure collaborator's insertion is successful
        r = TestClient.execute_one("""
                                   SELECT count(*) FROM collaborator WHERE user_id = %s
                                   """, [self.collaborator_id])
        self.assertGreater(r[0], 0)

        # make sure collaborator's removal is successful
        r = TestClient.delete('api/v1/projects/%s/collaborators/%s'
                              % (self.project_id, self.collaborator_id),
                              headers=TestClient.get_user_authorization(self.user_id))

        self.assertEqual(r['message'], 'Successfully removed user.')
        self.assertEqual(r['status'], 200)

        # check if database does not contain this collaborator anymore
        r = TestClient.execute_one("""
                                   SELECT count(*) FROM collaborator WHERE user_id = %s
                                   """, [self.collaborator_id])
        self.assertEqual(r[0], 0)

    def test_administrator_cannot_promote_self_to_owner(self):
        TestClient.execute("""
                           INSERT INTO "user" (id, github_id, username, avatar_url)
                           VALUES (%s, 2, %s, 'url1');
                           """, [self.collaborator_id,
                                     self.test_collaborator_data['username']])
        TestClient.execute("""
                           INSERT INTO collaborator (user_id, project_id, role)
                           VALUES (%s, %s, 'Administrator')
                           """, [self.collaborator_id, self.project_id])
        TestClient.opa_push()

        r = TestClient.app.put(
            'api/v1/projects/%s/collaborators/%s' % (self.project_id, self.collaborator_id),
            data=json.dumps({'role': 'Owner'}),
            headers=TestClient.get_user_authorization(self.collaborator_id),
            content_type='application/json')

        self.assertEqual(r.status_code, 403)
        self.assertEqual(json.loads(r.data)['message'], 'A project is limited to one owner.')
        role = TestClient.execute_one("""
                                      SELECT role FROM collaborator
                                      WHERE user_id = %s AND project_id = %s
                                      """, [self.collaborator_id, self.project_id])
        self.assertEqual(role[0], 'Administrator')
