import os
import base64
from unittest import TestCase

import eventlet
eventlet.monkey_patch()

import psycopg2
import psycopg2.extensions
import requests

from pyinfraboxutils.db import DB, connect_db
from pyinfraboxutils.token import encode_project_token
from pyinfraboxutils.ibopa import opa_push_all

conn = connect_db()
conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

class InputTests(TestCase):
    def get(self, url, password='b514af82-3c4f-4bb5-b1da-a89a0ced5e6f'):
        auth = base64.b64encode('infrabox:%s' % encode_project_token(password, '2514af82-3c4f-4bb5-b1da-a89a0ced5e6f', 'myproject'))
        headers = {'authorization': "Basic " + auth}
        return requests.get(url, headers=headers)

    def test_token_does_not_exist(self):
        r = self.get('http://docker-registry:8080/v2')
        self.assertEqual(r.status_code, 401)

class Test(TestCase):
    user_id = '1514af82-3c4f-4bb5-b1da-a89a0ced5e6f'
    project_id = '2514af82-3c4f-4bb5-b1da-a89a0ced5e6f'
    token = '3514af82-3c4f-4bb5-b1da-a89a0ced5e6f'
    foreign_project_id = '4514af82-3c4f-4bb5-b1da-a89a0ced5e6f'
    image_path = project_id + '/image_name'

    def _get_headers(self):
        auth = base64.b64encode('infrabox:%s' % encode_project_token(self.token, self.project_id, 'myproject'))
        headers = {'authorization': "Basic " + auth}
        return headers

    def get(self, url):
        return requests.get(url, headers=self._get_headers())

    def put(self, url):
        return requests.put(url, headers=self._get_headers())

    def post(self, url):
        return requests.post(url, headers=self._get_headers())

    def patch(self, url):
        return requests.patch(url, headers=self._get_headers())

    def delete(self, url):
        return requests.delete(url, headers=self._get_headers())

    def setUp(self):
        cur = conn.cursor()
        cur.execute('TRUNCATE auth_token')
        cur.execute('TRUNCATE project')
        cur.execute('TRUNCATE collaborator')
        cur.execute('''INSERT INTO auth_token (id, description, project_id, scope_push, scope_pull)
                        VALUES(%s, 'test token', %s, true, true)''', (self.token, self.project_id,))
        cur.execute('''INSERT INTO project(name, type, id)
                        VALUES('test', 'upload', %s)''', (self.project_id,))
        cur.execute('''INSERT INTO collaborator(project_id, user_id, role)
                        VALUES(%s, %s, 'Owner')''', (self.project_id, self.user_id))
        opa_push_all()

    def tearDown(self):
        cur = conn.cursor()
        cur.execute('''DELETE FROM auth_token''')
        cur.execute('''DELETE FROM collaborator''')
        cur.execute('''DELETE FROM project''')

    # /v2/
    def test_v2(self):
        "GET /v2/ should be accessible to every authenticated user"
        r = self.get('http://docker-registry:8080/v2/')
        self.assertEqual(r.status_code, 200)

    # /v2/_catalog
    def test_v2_catalog(self):
        "GET /v2/_catalog should not be accessible by anybody"
        r = self.get('http://docker-registry:8080/v2/_catalog')
        self.assertEqual(r.status_code, 401)

    # /v2/<name>/tags/list
    def test_v2_project_tags_list_get(self):
        "GET /v2/<p>/tags/list should be accessible by collaborators"
        r = self.get('http://docker-registry:8080/v2/%s/tags/list' % self.image_path)
        self.assertEqual(r.status_code, 200)

    def test_v2_project_tags_list_get_2(self):
        "GET /v2/<p>/tags/list/ should be accessible by collaborators"
        r = self.get('http://docker-registry:8080/v2/%s/tags/list/' % self.image_path)
        self.assertEqual(r.status_code, 200)

    def test_v2_project_tags_list_get_foreign(self):
        "GET /v2/<p>/tags/list should not be accessible by foreign users"
        r = self.get('http://docker-registry:8080/v2/%s/tags/list' % self.foreign_project_id)
        self.assertEqual(r.status_code, 401)

    def test_v2_project_tags_list_put(self):
        "PUT /v2/<p>/tags/list should NOT be accessible by collaborators"
        r = self.put('http://docker-registry:8080/v2/%s/tags/list' % self.image_path)
        self.assertEqual(r.status_code, 401)

    def test_v2_project_tags_list_delete(self):
        "DELETE /v2/<p>/tags/list should NOT be accessible by collaborators"
        r = self.delete('http://docker-registry:8080/v2/%s/tags/list' % self.image_path)
        self.assertEqual(r.status_code, 401)

    # /v2/<name>/manifests/<reference>
    def test_v2_project_manifests_reference_get(self):
        "GET /v2/<p>/manifests/<r> should be accessible by collaborators"
        r = self.get('http://docker-registry:8080/v2/%s/manifests/ref/' % self.image_path)
        self.assertEqual(r.status_code, 200)

    def test_v2_project_manifests_reference_put(self):
        "PUT /v2/<p>/manifests/<r> should not be accessible by collaborators"
        r = self.put('http://docker-registry:8080/v2/%s/manifests/ref/' % self.image_path)
        self.assertEqual(r.status_code, 401)

    def test_v2_project_manifests_reference_delete(self):
        "DELETE /v2/<p>/manifests/<r> should not be accessible by collaborators"
        r = self.delete('http://docker-registry:8080/v2/%s/manifests/ref/' % self.image_path)
        self.assertEqual(r.status_code, 401)

    # /v2/<name>/blobs/<digest>
    def test_v2_project_blobs_digest_get(self):
        "GET /v2/<p>/blobs/<d> should be accessible by collaborators"
        r = self.get('http://docker-registry:8080/v2/%s/blobs/digest/' % self.image_path)
        self.assertEqual(r.status_code, 200)

    def test_v2_project_blobs_digest_put(self):
        "PUT /v2/<p>/blobs/<d> should not be accessible by collaborators"
        r = self.put('http://docker-registry:8080/v2/%s/blobs/digest/' % self.image_path)
        self.assertEqual(r.status_code, 401)

    def test_v2_project_blobs_digest_delete(self):
        "DELETE /v2/<p>/blobs/<d> should not be accessible by collaborators"
        r = self.delete('http://docker-registry:8080/v2/%s/blobs/digest/' % self.image_path)
        self.assertEqual(r.status_code, 401)

    # /v2/<name>/blobs/upload/<uuid>
    def test_v2_project_blobs_upload_get(self):
        "GET /v2/<p>/blobs/upload/<uuid> should not be accessible by collaborators"
        r = self.get('http://docker-registry:8080/v2/%s/blobs/upload/uuid' % self.image_path)
        self.assertEqual(r.status_code, 200)

    def test_v2_project_blobs_upload_put(self):
        "PUT /v2/<p>/blobs/upload/<uuid> should not be accessible by collaborators"
        r = self.put('http://docker-registry:8080/v2/%s/blobs/upload/uuid' % self.image_path)
        self.assertEqual(r.status_code, 401)

    def test_v2_project_blobs_upload_delete(self):
        "DELETE /v2/<p>/blobs/upload/<uuid> should not be accessible by collaborators"
        r = self.delete('http://docker-registry:8080/v2/%s/blobs/upload/uuid' % self.image_path)
        self.assertEqual(r.status_code, 401)

    def test_v2_project_blobs_upload_patch(self):
        "DELETE /v2/<p>/blobs/upload/<uuid> should not be accessible by collaborators"
        r = self.patch('http://docker-registry:8080/v2/%s/blobs/upload/uuid' % self.image_path)
        self.assertEqual(r.status_code, 401)
