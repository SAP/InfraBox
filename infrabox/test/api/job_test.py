from os import stat, remove

import json

from temp_tools import TestClient
from test_template import ApiTestTemplate
from pyinfraboxutils.storage import storage


class JobTest(ApiTestTemplate):

    def test_get_job(self):
        r = TestClient.get('/api/v1/projects/%s/jobs/%s' % (self.project_id, self.job_id),
                           TestClient.get_project_authorization(self.user_id, self.project_id))
        self.assertEqual(r['id'], self.job_id)

    def test_get_job_manifest(self):
        r = TestClient.get('/api/v1/projects/%s/jobs/%s/manifest' % (self.project_id, self.job_id),
                           TestClient.get_project_authorization(self.user_id, self.project_id))
        self.assertEqual(r['id'], self.job_id)

    def test_get_job_output(self):
        job_data = {
            "version": 1,
            "subject": "subject_val",
            "status": "status_val1",
            "color": "green"
        }

        file_name = "test_get_job_output.tmp_test_file.json"
        with open(file_name, 'w') as job_data_file:
            # Write data into json file
            json.dump(job_data, job_data_file)

        file_size = stat(file_name).st_size
        with open(file_name, 'r') as job_data_file:
            storage.upload_output(stream=job_data_file, key=self.job_id + '.tar.gz')
        remove(file_name)

        res = TestClient.get('/api/v1/projects/%s/jobs/%s/output' % (self.project_id, self.job_id),
                           TestClient.get_project_authorization(self.user_id, self.project_id))

        file_name = file_name + '.out_test'
        with open(file_name, "wb") as output_file:
            output_file.write(res.data)
            out_size = output_file.tell()
        remove(file_name)

        self.assertEqual(out_size, file_size)
