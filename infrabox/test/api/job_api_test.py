from os import getcwd, stat

from pyinfraboxutils.token import encode_job_token
from temp_tools import TestClient
from test_template import ApiTestTemplate


class JobApiTest(ApiTestTemplate):

    url_ns = 'api/job'

    #def test_uuid_validation(self):
    #   pass
    #   #TODO

    #def test_job(self):
    #   result = TestClient.get(self.url_ns + '/job', self.job_headers)
    #   self.assertEqual(result['project']['id'], self.project_id)
    #   self.assertEqual(result['job']['id'], self.job_id)

    #def test_source(self):
    #   result = TestClient.get(self.url_ns + '/source', self.job_headers)
    #   print result

    def test_cache(self):
        filename = 'cache.tar.gz'

        file_path = getcwd() + '/' + filename

        test_data = open(file_path, 'rb')
        files = {'cache.tar.gz': test_data}

        result = TestClient.post(self.url_ns + '/cache', data=files, headers=self.job_headers,
                                 content_type='multipart/form-data')

        self.assertEqual(result, {})

        result = TestClient.get(self.url_ns + '/cache', self.job_headers)

        actual_cache_size = stat(file_path).st_size

        with open('received_cache', 'wb') as rec_cache:
            rec_cache.write(result.data)
            received_cache_size = rec_cache.tell()


        self.assertEqual(received_cache_size, actual_cache_size)

    def test_output(self):
        filename = 'output.tar.gz'

        file_path = getcwd() + '/' + filename

        test_data = open(file_path, 'rb')
        files = {'output.tar.gz': test_data}

        result = TestClient.post(self.url_ns + '/output', data=files, headers=self.job_headers,
                                 content_type='multipart/form-data')

        self.assertEqual(result, {})
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
