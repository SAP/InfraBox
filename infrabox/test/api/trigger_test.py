from temp_tools import TestClient
from test_template import ApiTestTemplate
from pyinfraboxutils.storage import storage
from os import getcwd, stat

class TriggerTest(ApiTestTemplate):

    def test_repo_does_not_exist(self):
        d = {
            'branch_or_sha': 'master',
            'sha': 'master'
        }

        TestClient.execute('TRUNCATE repository')

        r = TestClient.post('/api/v1/projects/%s/trigger' % self.project_id, data=d,
                            headers=TestClient.get_user_authorization(self.user_id))
        self.assertEqual(r['message'], 'Build triggered')
        result = TestClient.execute_many('SELECT * FROM build WHERE id != %s', [self.build_id])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['build_number'], 2)

    def test_trigger_successfully(self):

        d = {
            'branch_or_sha': 'master'
        }

        r = TestClient.post('/api/v1/projects/%s/trigger' % (self.project_id), headers=TestClient.get_user_authorization(self.user_id), data=d)
        self.assertEqual(r['status'], 200)
        self.assertEqual(r['message'], 'Build triggered')
