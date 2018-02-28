import unittest
import mock

from xmlrunner import XMLTestRunner

from pyinfraboxutils.ibmock import MockResponse

from test_template import ApiTestTemplate

from temp_tools import TestClient
from job_api_test import JobApiTest
from build_test import BuildTest
from job_test import JobTest

from pyinfraboxutils.storage import storage

class ApiTestCase(ApiTestTemplate):

    def test_get_project_does_not_exist(self):
        r = TestClient.get('/api/v1/projects/%s' % self.repo_id, TestClient.get_user_authorization(self.user_id))
        self.assertEqual(r['message'], 'Unauthorized')

    def test_get_project(self):
        #TestClient.execute('''
        #    INSERT INTO job (id, state, build_id, type, name, project_id,
        #                     build_only, dockerfile, cpu, memory)
        #    VALUES (gen_random_uuid(), 'queued', %s, 'create_job_matrix',
        #            'Create Jobs', %s, false, '', 1, 1024)
        #''', [self.build_id, self.project_id])
##
        #TestClient.execute('''
        #    INSERT INTO build (id, commit_id, build_number, project_id)
        #    VALUES (%s, %s, 1, %s)
        #''', [self.build_id, self.sha, self.project_id])

        r = TestClient.get('/api/v1/projects/%s' % self.project_id, TestClient.get_user_authorization(self.user_id))
        self.assertEqual(r['id'], self.project_id)

    def test_repo_does_not_exist(self):
        d = {
            'branch_or_sha': 'master',
            'sha': 'master'
        }

        TestClient.execute('TRUNCATE repository')

        r = TestClient.post('/api/v1/projects/%s/trigger' % self.project_id, data=d, headers=TestClient.get_user_authorization(self.user_id))
        self.assertEqual(r['message'], 'Build triggered')
        result = TestClient.execute_many('SELECT * FROM build WHERE id != %s', [self.build_id])
        print result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['build_number'], 2)


    #@mock.patch('requests.post')
    def test_trigger_successfully(self):

        d = {
            'branch_or_sha': 'master'
        }

        r = TestClient.post('/api/v1/projects/%s/trigger' % (self.project_id), headers=TestClient.get_user_authorization(self.user_id), data=d)
        print r
        self.assertEqual(r['status'], 200)
        self.assertEqual(r['message'], 'Build triggered')



if __name__ == '__main__':
    storage.create_buckets()

    with open('results.xml', 'wb') as output:
        #unittest.main(testRunner=xmlrunner.XMLTestRunner(output=output))
        suite1 = unittest.TestLoader().loadTestsFromTestCase(ApiTestCase)
        #suite2 = unittest.TestLoader().loadTestsFromTestCase(JobApiTest)
        #suite3 = unittest.TestLoader().loadTestsFromTestCase(BuildTest)
        #suite4 = unittest.TestLoader().loadTestsFromTestCase(JobTest)
        runner = XMLTestRunner(output=output)
        runner.run(suite1)
        #runner.run(suite2)
        #runner.run(suite3)
        #runner.run(suite4)
#
