import unittest
import json
import mock
from api import server
import xmlrunner

from pyinfraboxutils.db import connect_db
from pyinfraboxutils.token import encode_user_token
from pyinfraboxutils.ibmock import MockResponse

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
            'branch': 'master',
            'sha': 'master'
        }

        self.execute('TRUNCATE repository')
        r = self.post('/api/v1/projects/%s/trigger' % self.project_id, d)
        self.assertEqual(r['message'], 'repo not found')

    def test_upload_successfully(self):
        self.execute('''
            INSERT INTO build (source_upload_id, build_number, project_id)
            VALUES (%s, 1, %s);
            UPDATE project SET type='upload';
        ''', [self.project_id, self.project_id])

        r = self.post('/api/v1/projects/%s/trigger' % self.project_id, {})
        self.assertEqual(r['status'], 200)

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

    def get_project_headers(self): # pragma: no cover
        token = encode_user_token(self.user_id)
        h = {'Authorization': 'token %s' % token}
        return h

    def get(self, url, headers=None): # pragma: no cover
        if not headers:
            headers = self.get_project_headers()

        r = self.app.get(url, headers=headers)

        if r.mimetype == 'application/json':
            j = json.loads(r.data)
            return j

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
    with open('results.xml', 'wb') as output:
        unittest.main(testRunner=xmlrunner.XMLTestRunner(output=output))
