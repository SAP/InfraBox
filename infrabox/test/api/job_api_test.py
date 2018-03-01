from os import getcwd, stat, remove

from pyinfraboxutils.token import encode_job_token
from temp_tools import TestClient
from test_template import ApiTestTemplate


class JobApiTest(ApiTestTemplate):

    url_ns = 'api/job'

    #def test_uuid_validation(self):
    #   pass
    #   #TODO

    def test_job(self):
        filename = 'test_file1.json'
        file_path = getcwd() + '/' + filename
        filesize = stat(file_path).st_size
        TestClient.execute("""TRUNCATE source_upload""")

        TestClient.execute("""INSERT INTO source_upload (id, project_id, filename, filesize)
                           VALUES (%s, %s, %s, %s);
                           """, (self.source_upload_id, self.project_id, filename, filesize))
        result = TestClient.get(self.url_ns + '/job', self.job_headers)
        self.assertEqual(result['project']['id'], self.project_id)
        self.assertEqual(result['job']['id'], self.job_id)

    def test_source(self):
        filename = 'test_file1.json'
        file_path = getcwd() + '/' + filename
        filesize = stat(file_path).st_size

        TestClient.execute("""TRUNCATE source_upload""")

        TestClient.execute("""INSERT INTO source_upload (id, project_id, filename, filesize)
                           VALUES (%s, %s, %s, %s);
                           """, (self.source_upload_id, self.project_id, filename, filesize))

        TestClient.execute("""UPDATE build SET source_upload_id = %s WHERE
                           id = %s""", (self.source_upload_id, self.build_id))

        with open(file_path, 'rb') as source_data:
            storage.upload_project(source_data, filename)

            response = TestClient.get(self.url_ns + '/source', self.job_headers)

        with open('test_source_response', 'wb') as response_data:
            response_data.write(response.data)
            response_size = response_data.tell()
            response_data.close()
        remove('test_source_response')

        self.assertEqual(response_size, filesize)

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

    def test_setrunning(self):
        result = TestClient.post(self.url_ns + '/setrunning', {}, self.job_headers)
        self.assertEqual(result, {})

    def test_create_jobs(self):
        data = {"jobs": [{
            "id": "6544af82-1c4f-5bb5-b1da-a54a0ced5e6f",
            "type": "docker",
            "name": "test_job1",
            "docker_file": "",
            "build_only": False,
            "resources": {"limits": {"cpu": 1, "memory": 512}}
            }]}
        result = TestClient.post(self.url_ns + '/create_jobs', data, self.job_headers)
        self.assertEqual(result, 'Successfully create jobs')

    def test_consoleupdate(self):
        data = {"output": "some test output"}
        result = TestClient.post(self.url_ns + '/consoleupdate', data, self.job_headers)
        self.assertEqual(result, {})

    def test_stats(self):
        data = {"stats": "finished"}
        result = TestClient.post(self.url_ns + '/stats', data, self.job_headers)
        self.assertEqual(result, {})

    def test_markup(self):
        data = {}
        result = TestClient.post(self.url_ns + '/markup', data, self.job_headers)
        self.assertEqual(result, {})

    def test_badge(self):

        TestClient.execute("""TRUNCATE job_badge""")

        filename1 = 'test_file1.json'
        file_path1 = getcwd() + '/' + filename1
        file1 = open(file_path1)

        data = {"file1": file1}
        result = TestClient.post(self.url_ns + '/badge', data=data, headers=self.job_headers,
                                 content_type='multipart/form-data')
        file1.close()

        self.assertEqual(result, {})

    def test_testresult(self):

        #test empty data
        data = {"data": {}}

        result = TestClient.post(self.url_ns + '/testresult', data=data, headers=self.job_headers)

        self.assertEqual(result['message'], 'data not set')
        #self.assertEqual(result['status'], 400)

        # test wrong file format
        test_filename = 'dummy_results.xml'
        test_file_path = getcwd() + '/' + test_filename
        test_file = open(test_file_path, 'r')
        data = {"data": test_file}

        result = TestClient.post(self.url_ns + '/testresult', data=data, headers=self.job_headers,
                                 content_type='multipart/form-data')

        self.assertEqual(result['message'], 'file ending not allowed')
        #self.assertEqual(result['status'], 400)

        # test data
        test_filename = 'dummy_test_result.json'
        test_file_path = getcwd() + '/' + test_filename
        test_file = open(test_file_path, 'r')

        TestClient.execute("""TRUNCATE test_run""")

        data = {"data": test_file}
        result = TestClient.post(self.url_ns + '/testresult', data=data, headers=self.job_headers,
                                 content_type='multipart/form-data')

        test_file.close()

        self.assertEqual(result, {})

    def test_setfinished(self):
        data = {"state": "finished",
                "message": "Job successfully finished"
                }
        result = TestClient.post(self.url_ns + '/setfinished', data, self.job_headers)
        self.assertEqual(result, {})

