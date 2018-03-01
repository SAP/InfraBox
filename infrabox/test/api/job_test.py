from temp_tools import TestClient
from test_template import ApiTestTemplate
from pyinfraboxutils.storage import storage
from os import getcwd, stat

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

        file_name = '/test_file1.json'
        file_path = getcwd() + file_name
        file = open(file_path, 'r')
        file_size = stat(file_path).st_size

        storage.upload_output(stream=file, key=self.job_id + '.tar.gz')


        res = TestClient.get('/api/v1/projects/%s/jobs/%s/output' % (self.project_id, self.job_id),
                           TestClient.get_project_authorization(self.user_id, self.project_id))

        with open(file_path + '.out_test', "wb") as output_file:

            output_file.write(res.data)
            out_size = output_file.tell()

        self.assertEqual(out_size, file_size)
