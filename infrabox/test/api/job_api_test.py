
from os import getcwd, stat

from pyinfraboxutils.token import encode_job_token
from temp_tools import TestClient
from test_template import ApiTestTemplate


class JobApiTest(ApiTestTemplate):

    url_ns = 'api/job'

    #ef test_uuid_validation(self):
    #   pass
    #   #TODO

    #ef test_job(self):
    #   result = TestClient.get(self.url_ns + '/job', self.job_headers)
    #   self.assertEqual(result['project']['id'], self.project_id)
    #   self.assertEqual(result['job']['id'], self.job_id)

    #ef test_source(self):
    #   result = TestClient.get(self.url_ns + '/source', self.job_headers)
    #   print result

    def test_cache(self):

        template = 'project_%s_job_%s.tar.gz'
        key = template % (self.project_id, self.job_name)
        key = key.replace('/', '_')

        test_data = open(getcwd() + '/cache.tar.gz', 'rb')

        result = TestClient.post(self.url_ns + '/cache', test_data, self.job_headers, content_type='application/files')

        print '\n\n\n\n\n\n\n\n\ncache post result', result

        result = TestClient.get(self.url_ns + '/cache', self.job_headers)

        print 'Cache result', result

    #def test_output(self):
    #    test_data = {"test_name1": 'test_vav1'}
    #    result = TestClient.post(self.url_ns + '/output', test_data, self.job_headers)
    #    print 'Output result', result
#
    #def test_setrunning(self):
    #    result = TestClient.post(self.url_ns + '/setrunning', {}, self.job_headers)
    #    self.assertEqual(result, {})
#
    #def test_create_jobs(self):
    #    data = {"jobs": [{
    #        "id": "6544af82-1c4f-5bb5-b1da-a54a0ced5e6f",
    #        "type": "docker",
    #        "name": "test_job1",
    #        "docker_file": "",
    #        "build_only": False,
    #        "resources": {"limits": {"cpu": 1, "memory": 512}}
    #        }]}
    #    result = TestClient.post(self.url_ns + '/create_jobs', data, self.job_headers)
    #    self.assertEqual(result, 'Successfully create jobs')
#
    #def test_consoleupdate(self):
    #    data = {"output": "some test output"}
    #    result = TestClient.post(self.url_ns + '/consoleupdate', data, self.job_headers)
    #    self.assertEqual(result, {})
#
    #def test_stats(self):
    #    data = {"stats": "finished"}
    #    result = TestClient.post(self.url_ns + '/stats', data, self.job_headers)
    #    self.assertEqual(result, {})
#
    #def test_markup(self):
    #    data = {}
    #    result = TestClient.post(self.url_ns + '/markup', data, self.job_headers)
    #    self.assertEqual(result, {})
#
    #def test_badge(self):
    #    data = {}
    #    result = TestClient.post(self.url_ns + '/badge', data, self.job_headers)
    #    self.assertEqual(result, {})
#
    #def test_testresult(self):
    #    test_file1 = getcwd() + '/test_file1.json'
#
    #    data = {"data": {}}
#
    #    result = TestClient.post(self.url_ns + '/testresult', data=data, headers=self.job_headers)
    #    self.assertEqual(result['message'], 'data not set')
    #    self.assertEqual(result['status'], 400)
#
    #    with open(test_file1, 'r') as f:
    #        result = TestClient.post(self.url_ns + '/testresult', files=f, headers=self.job_headers)
#
    #    print 'TR', result
#
    #def test_setfinished(self):
    #    data = {"status": "finished",
    #            "message": "Job successfully finished"
    #            }
    #    result = TestClient.post(self.url_ns + '/setfinished', data, self.job_headers)
    #    print 'TF', self.assertEqual(result, {})
#
