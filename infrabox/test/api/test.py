import unittest
import json
import mock
from api import server
import xmlrunner

from pyinfraboxutils.db import connect_db
from pyinfraboxutils.token import encode_user_token, encode_job_token
from pyinfraboxutils.ibmock import MockResponse

from pyinfraboxutils.storage import storage

class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = server.app.test_client()
        server.app.testing = True
        self.conn = connect_db()

        self.execute('TRUNCATE "user"')
        self.execute('TRUNCATE project')
        self.execute('TRUNCATE collaborator')
        self.execute('TRUNCATE repository')
        self.execute('TRUNCATE commit')
        self.execute('TRUNCATE build')
        self.execute('TRUNCATE job')

        self.project_id = '1514af82-3c4f-4bb5-b1da-a89a0ced5e6f'
        self.user_id = '2514af82-3c4f-4bb5-b1da-a89a0ced5e6f'
        self.repo_id = '3514af82-3c4f-4bb5-b1da-a89a0ced5e6f'
        self.build_id = '4514af82-3c4f-4bb5-b1da-a89a0ced5e6f'
        self.job_id1 = '5514af82-3c4f-4bb5-b1da-a89a0ced5e6f'
        self.job_id2 = '6514af82-3c4f-4bb5-b1da-a89a0ced5e6f'
        self.sha = 'd670460b4b4aece5915caf5c68d12f560a9fe3e4'

        self.execute("""
            INSERT INTO collaborator (user_id, project_id, owner)
            VALUES (%s, %s, true);
        """, (self.user_id, self.project_id))

        self.execute("""
            INSERT INTO "user" (id, github_id, username,
                avatar_url)
            VALUES (%s, 1, 'testuser', 'url');
        """, (self.user_id,))

        self.execute("""
            INSERT INTO project(id, name, type)
            VALUES (%s, 'testproject', 'gerrit');
        """, (self.project_id,))

        self.execute("""
            INSERT INTO repository(id, name, html_url, clone_url, github_id, project_id, private)
            VALUES (%s, 'testrepo', 'url', 'clone_url', 0, %s, true);
        """, (self.repo_id, self.project_id))

        self.execute("""
            INSERT INTO job(id, state, build_id, type, name, project_id, build_only, cpu, memory)
            VALUES (%s, 'finished', %s, 'run_project_container', 'job1', %s, true, 1, 1024);
        """, (self.job_id1, self.build_id, self.project_id))

        self.execute("""
            INSERT INTO job(id, state, build_id, type, name, project_id, build_only, cpu, memory, dependencies)
            VALUES (%s, 'running', %s, 'run_project_container', 'job2', %s, true, 1, 1024, %s);
        """, (self.job_id2, self.build_id, self.project_id, json.dumps([{'job': 'job1', 'job-id': self.job_id1}])))


    def execute(self, stmt, args=None):
        cur = self.conn.cursor()
        cur.execute(stmt, args)
        cur.close()
        self.conn.commit()

    def test_get_project_does_not_exist(self):
        r = self.get('/api/v1/projects/%s' % self.repo_id)
        self.assertEqual(r['message'], 'Unauthorized')

    def test_get_project(self):
        self.execute('''
            INSERT INTO job (id, state, build_id, type, name, project_id,
                             build_only, dockerfile, cpu, memory)
            VALUES (gen_random_uuid(), 'queued', %s, 'create_job_matrix',
                    'Create Jobs', %s, false, '', 1, 1024)
        ''', [self.build_id, self.project_id])

        self.execute('''
            INSERT INTO build (id, commit_id, build_number, project_id)
            VALUES (%s, %s, 1, %s)
        ''', [self.build_id, self.sha, self.project_id])

        r = self.get('/api/v1/projects/%s' % self.project_id)
        self.assertEqual(r['id'], self.project_id)

    def test_repo_does_not_exist(self):
        d = {
            'branch_or_sha': 'master',
            'sha': 'master'
        }

        self.execute('TRUNCATE repository')
        r = self.post('/api/v1/projects/%s/trigger' % self.project_id, d)
        self.assertEqual(r['message'], 'repo not found')

    @mock.patch('requests.post')
    def test_trigger_successfully(self, mocked):
        mocked.return_value = MockResponse(200, {
            'sha': self.sha,
            'message': 'message',
            'branch': 'branch',
            'author': {
                'name': 'name',
                'email': 'email'
            },
            'url': 'url',
        })

        d = {
            'branch_or_sha': 'master'
        }

        r = self.post('/api/v1/projects/%s/trigger' % (self.project_id), d)
        self.assertEqual(r['status'], 200)
        self.assertEqual(r['message'], 'Build triggered')

    def test_get_output(self):
        r = self.get('/api/job/output/%s' % (self.job_id1), headers=self.get_job_headers(self.job_id2), status=404)

    def get_project_headers(self): # pragma: no cover
        token = encode_user_token(self.user_id)
        h = {'Authorization': 'token %s' % token}
        return h

    def get_job_headers(self, job_id): # pragma: no cover
        token = encode_job_token(job_id)
        h = {'Authorization': 'token %s' % token}
        return h

    def get(self, url, headers=None, status=None): # pragma: no cover
        if not headers:
            headers = self.get_project_headers()

        r = self.app.get(url, headers=headers)

        if r.mimetype == 'application/json':
            j = json.loads(r.data)
            return j

        if status:
            self.assertEqual(status, r.status_code)

        return r


    def post(self, url, data, headers=None): # pragma: no cover
        if not headers:
            headers = self.get_project_headers()

        r = self.app.post(url,
                          data=json.dumps(data),
                          headers=headers,
                          content_type='application/json')

        if r.mimetype == 'application/json':
            j = json.loads(r.data)
            return j

        return r

if __name__ == '__main__':
    storage.create_buckets()

    with open('results.xml', 'wb') as output:
        unittest.main(testRunner=xmlrunner.XMLTestRunner(output=output))
