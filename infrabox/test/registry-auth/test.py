import eventlet
eventlet.monkey_patch()

import unittest
import json
import base64
from auth import server
import xmlrunner
import psycopg2
import psycopg2.extensions

from pyinfraboxutils.ibopa import opa_push_all
from pyinfraboxutils.db import  DB, connect_db
from pyinfraboxutils.token import encode_project_token

conn = connect_db()
conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

class AccountTestCase(unittest.TestCase):

    def setUp(self):
        self.app = server.app.test_client()
        server.app.testing = True

        self.project_id = 'a514af82-3c4f-4bb5-b1da-a89a0ced5e6f'
        self.project_token = 'bb14af82-3c4f-4bb5-b1da-a89a0ced5e6f'
        self.job_id = 'c514af82-3c4f-4bb5-b1da-a89a0ced5e6f'

        cur = conn.cursor()
        cur.execute('TRUNCATE auth_token')
        cur.execute('TRUNCATE project')
        cur.execute('''INSERT INTO project(name, type, id)
                        VALUES('test', 'upload', %s)''', (self.project_id,))
        opa_push_all()

    def tearDown(self):
        cur = conn.cursor()
        cur.execute('''DELETE FROM auth_token''')
        cur.execute('''DELETE FROM project''')

    def test_no_token(self):
        r = self.get('/v2')
        self.assertEqual(r['status'], 401)

    def test_header_no_basic(self):
        h = {'Authorization': 'some value'}
        r = self.get('/v2', h)
        self.assertEqual(r['status'], 401)

    def test_header_no_value_after_basic(self):
        h = {'Authorization': 'Basic'}
        r = self.get('/v2', h)
        self.assertEqual(r['status'], 401)

    def test_header_invalid_token(self):
        h = {'Authorization': 'Basic infrabox:someweirdvalue'}
        r = self.get('/v2', h)
        self.assertEqual(r['status'], 401)

    def test_header_no_password(self):
        h = {'Authorization': 'Basic %s' % base64.b64encode('infrabox')}
        r = self.get('/v2', h)
        self.assertEqual(r['status'], 401)

    def test_header_no_password_2(self):
        h = {'Authorization': 'Basic %s' % base64.b64encode('infrabox:2')}
        r = self.get('/v2', h)
        self.assertEqual(r['status'], 401)

    def test_project_token_doest_not_exist(self):
        r = self.get('/v2', self.get_project_headers())
        self.assertEqual(r['status'], 401)

    def test_v2_valid_token(self):
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO auth_token (id, project_id, description)
            VALUES (%s, %s, 'desc')
        ''', [self.project_token, self.project_id])

        r = self.get('/v2', self.get_project_headers())
        self.assertEqual(r['status'], 200)

    def test_path_no_headers(self):
        r = self.get('/v2/%s' % self.project_id)
        self.assertEqual(r['status'], 401)

    def test_path_invalid_repo_name(self):
        r = self.get('/v2/%s' % self.project_id, self.get_project_headers())
        self.assertEqual(r['status'], 401)

    def test_path_wrong_method(self):
        r = self.get('/v2/%s/%s' % (self.project_id, self.job_id),
                     self.get_project_headers(), method='POST')
        self.assertEqual(r['status'], 401)

    def test_path_invalid_repo_name_and_job_name(self):
        try:
            self.get('/v2/hello/world', self.get_project_headers())
        except psycopg2.DataError:
            pass

    def test_path_unknown_token(self):
        r = self.get('/v2/%s/%s' % (self.project_id, self.job_id), self.get_project_headers())
        self.assertEqual(r['status'], 401)

    def test_path_valid_token(self):
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO auth_token (id, project_id, description)
            VALUES (%s, %s, 'desc')
        ''', [self.project_token, self.project_id])

        print("valid project token")

        r = self.get('/v2/%s/%s' % (self.project_id, self.job_id), self.get_project_headers())
        self.assertEqual(r['status'], 200)

    def get_project_headers(self, project_token=None): # pragma: no cover
        if not project_token:
            project_token = self.project_token

        token = encode_project_token(project_token, self.project_id, 'myproject')
        h = {'Authorization': 'Basic %s' % base64.b64encode('infrabox:%s' % token)}
        return h

    def get(self, url, headers=None, method='GET'): # pragma: no cover
        if headers:
            headers['X-Original-Method'] = method

        r = self.app.get(url, headers=headers)

        if r.mimetype == 'application/json':
            return json.loads(r.data)

        return r

if __name__ == '__main__':
    with open('results.xml', 'wb') as output:
        unittest.main(testRunner=xmlrunner.XMLTestRunner(output=output))
