from os import getcwd, stat, remove

import json

from pyinfraboxutils.storage import storage
from temp_tools import TestClient, TestUtils
from test_template import ApiTestTemplate


class JobApiTest(ApiTestTemplate):

    url_ns = 'api/job'

    def test_job(self):
        filename = 'temp_file.json'
        filesize = 100

        TestClient.execute("""INSERT INTO source_upload (id, project_id, filename, filesize)
                           VALUES (%s, %s, %s, %s)
                           """, [self.source_upload_id, self.project_id, filename, filesize])
        r = TestClient.get(self.url_ns + '/job', self.job_headers)
        self.assertEqual(r['project']['id'], self.project_id)
        self.assertEqual(r['job']['id'], self.job_id)

    def test_source(self):
        data = {"data": "dummy_data"}
        file_name = "test_source.tmp_test_file"

        with open(file_name, "w") as source_data_file:
            json.dump(data, source_data_file)

        file_size = stat(file_name).st_size

        TestClient.execute("""INSERT INTO source_upload (id, project_id, filename, filesize)
                              VALUES (%s, %s, %s, %s)
                           """, [self.source_upload_id, self.project_id, file_name, file_size])

        TestClient.execute("""UPDATE build SET source_upload_id = %s
                              WHERE id = %s""", [self.source_upload_id, self.build_id])

        with open(file_name, 'r') as source_data:
            storage.upload_project(source_data, file_name)
        remove(file_name)

        response = TestClient.get(self.url_ns + '/source', self.job_headers)
        response_size = TestUtils.get_stream_file_size(response.data)
        self.assertEqual(response_size, file_size)

    def test_cache(self):
        filename = 'cache.tar.snappy'

        file_path = getcwd() + '/' + filename

        test_data = open(file_path, 'rb')
        files = {'cache.tar.snappy': test_data}

        r = TestClient.post(self.url_ns + '/cache', data=files, headers=self.job_headers,
                            content_type='multipart/form-data')
        self.assertEqual(r, {})

        r = TestClient.get(self.url_ns + '/cache?filename=%s' % filename, headers=self.job_headers)
        actual_cache_size = stat(file_path).st_size
        received_cache_size = TestUtils.get_stream_file_size(r.data)

        # Ensure downloaded and uploaded file sizes are equal
        self.assertEqual(received_cache_size, actual_cache_size)

    def test_output(self):
        filename = 'output.tar.snappy'

        file_path = getcwd() + '/' + filename

        test_data = open(file_path, 'rb')
        files = {'output.tar.snappy': test_data}

        r = TestClient.post(self.url_ns + '/output', data=files, headers=self.job_headers,
                            content_type='multipart/form-data')
        self.assertEqual(r, {})

    def test_create_jobs(self):
        job_id = "6544af82-1c4f-5bb5-b1da-a54a0ced5e6f"
        data = {"jobs": [{
            "id": job_id,
            "type": "docker",
            "name": "test_job1",
            "docker_file": "",
            "build_only": False,
            "resources": {"limits": {"cpu": 1, "memory": 512}}
        }]}
        r = TestClient.post(self.url_ns + '/create_jobs', data, self.job_headers)
        self.assertEqual(r, 'Successfully create jobs')

        jobs = TestClient.execute_many("""SELECT id, name, type FROM job
                                          WHERE id = %s""", [job_id])
        self.assertEqual(jobs[0][0], data["jobs"][0]["id"])
        self.assertEqual(jobs[0][1], self.job_name + "/" + data["jobs"][0]["name"])
        # If type was equal to "docker" then it should replace it with "run_project_container" type
        self.assertEqual(jobs[0][2], "run_project_container")

        num_jobs = len(jobs)
        self.assertEqual(num_jobs, 1)

    def test_stats(self):
        data = {"stats": {}}
        r = TestClient.post(self.url_ns + '/stats', data=data, headers=self.job_headers)
        self.assertEqual(r, {})

        r = TestClient.execute_one("""SELECT stats FROM job
                                       WHERE id = %s""", [self.job_id])
        self.assertEqual(r["stats"], '%s' % data["stats"])

    def test_markup(self):
        markup_data = {
            "version": 1,
            "title": "dummy_title",
            "elements": [{
                "type": "text",
                "text": "dummy_text"
            }]
        }
        file_name = "test_markup.tmp_test_file.json"

        with open(file_name, 'w') as markup_data_file:
            json.dump(markup_data, markup_data_file)

        with open(file_name, 'r') as markup_data_file:
            markup_data_file.seek(0)
            data = {"file1": markup_data_file}
            r = TestClient.post(self.url_ns + '/markup', data=data, headers=self.job_headers,
                                content_type='multipart/form-data')
        remove(file_name)
        self.assertEqual(r, {})

        r = TestClient.execute_one("""SELECT job_id, project_id, name, data FROM job_markup
                                       WHERE job_id = %s""", [self.job_id])
        # check job_id
        self.assertEqual(r[0], self.job_id)
        # check project_id
        self.assertEqual(r[1], self.project_id)
        # check name
        self.assertEqual(r[2], "file1")
        received_data = json.loads(r[3])
        # check data (title)
        self.assertEqual(received_data["title"], markup_data["title"])
        # check data (elements)
        self.assertEqual(received_data["elements"], markup_data["elements"])

    def test_badge(self):
        job_data = {
            "version": 1,
            "subject": "subject_val",
            "status": "status_val1",
            "color": "green"
        }

        file_name = "test_badge.tmp_test_file.json"
        with open(file_name, 'w') as job_data_file:
            # Write data into json file
            json.dump(job_data, job_data_file)

        with open(file_name, 'r') as job_data_file:
            data = {"file1": job_data_file}
            result = TestClient.post(self.url_ns + '/badge', data=data, headers=self.job_headers,
                                     content_type='multipart/form-data')
        remove(file_name)
        self.assertEqual(result, {})

        r = TestClient.execute_one("""SELECT * from job_badge
                                       WHERE job_id = %s""", [self.job_id])
        self.assertEqual(r["job_id"], self.job_id)
        self.assertEqual(r["project_id"], self.project_id)
        self.assertEqual(r["subject"], job_data["subject"])
        self.assertEqual(r["status"], job_data["status"])
        self.assertEqual(r["color"], job_data["color"])

    def test_testresult(self):
        #test empty data
        data = {"data": {}}
        result = TestClient.post(self.url_ns + '/testresult', data=data, headers=self.job_headers)
        self.assertEqual(result['message'], 'data not set')

        # test wrong file format
        test_filename = 'dummy_results.xml'
        with open(test_filename, 'w') as test_file:
            # just create file, there's no need to write anything into file
            pass

        with open(test_filename, 'r') as test_file:
            data = {"data": test_file}
            r = TestClient.post(self.url_ns + '/testresult', data=data, headers=self.job_headers,
                                content_type='multipart/form-data')
        self.assertEqual(r['message'], 'file ending not allowed')
        remove(test_filename)

        # test data
        testresult_data = {
            "version": 1,
            "tests": [
                {
                    "suite":"api_test_suite",
                    "name": "test_name1",
                    "status": "ok",
                    "duration": 5,
                    "message": "test_message1",
                    "stack":"stack1",
                    "measurements":[]
                }, {
                    "suite":"api_test_suite",
                    "name": "test_name2",
                    "status": "failure",
                    "duration": 21,
                    "message": "test_message2",
                    "stack":"stack2",
                    "measurements":[]
                }]
        }
        test_filename = 'dummy_test_result.json'
        with open(test_filename, 'w') as test_file:
            json.dump(testresult_data, test_file)

        TestClient.execute("""TRUNCATE test_run""")

        with open(test_filename, 'r') as test_file:
            data = {"data": test_file}
            r = TestClient.post(self.url_ns + '/testresult', data=data, headers=self.job_headers,
                                content_type='multipart/form-data')
        self.assertEqual(r, {})
        remove(test_filename)

        r = TestClient.execute_many("""SELECT state, duration, message, stack FROM test_run
                                       WHERE job_id = %s""", [self.job_id])

        # We receive doubles from the SQL query results so we need to convert values manually to be able to test it
        for test in testresult_data["tests"]:
            test["duration"] = float(test["duration"])

        keys = ['status', 'duration', 'message', 'stack']
        for i, received_row in enumerate(r):
            # create dictionary from the list to compare it easier
            row_dictionary = dict(zip(keys, received_row))
            self.assertTrue(all(item in testresult_data["tests"][i].items()
                                for item in row_dictionary.items()))
