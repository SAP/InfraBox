import os
import base64
from unittest import TestCase

import psycopg2
import psycopg2.extensions
import requests

conn = psycopg2.connect(dbname=os.environ['INFRABOX_DATABASE_DB'],
                        host=os.environ['INFRABOX_DATABASE_HOST'],
                        port=os.environ['INFRABOX_DATABASE_PORT'],
                        user=os.environ['INFRABOX_DATABASE_USER'],
                        password=os.environ['INFRABOX_DATABASE_PASSWORD'])

conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

class InputTests(TestCase):
    def get(self, url, username='infrabox', password='b514af82-3c4f-4bb5-b1da-a89a0ced5e6f'):
        auth = base64.b64encode('%s:%s' % (username, password,))
        headers = {'authorization': "Basic " + auth}
        return requests.get(url, headers=headers)

    def test_token_does_not_exist(self):
        r = self.get('http://docker-registry:8080/v2')
        assert r.status_code == 401

    def test_username_not_valid_uuid(self):
        r = self.get('http://docker-registry:8080/v2', '3c4f-4bb5-b1da-a89a0ced5e6f', 'b514af82-3c4f-4bb5-b1da-a89a0ced5e6f')
        assert r.status_code == 401

    def test_password_not_valid_uuid(self):
        r = self.get('http://docker-registry:8080/v2', 'b514af82-3c4f-4bb5-b1da-a89a0ced5e6f', '3c4f-4bb5-b1da-a89a0ced5e6f')
        assert r.status_code == 401

class Test(TestCase):
    user_id = '1514af82-3c4f-4bb5-b1da-a89a0ced5e6f'
    project_id = '2514af82-3c4f-4bb5-b1da-a89a0ced5e6f'
    token = '3514af82-3c4f-4bb5-b1da-a89a0ced5e6f'
    foreign_project_id = '4514af82-3c4f-4bb5-b1da-a89a0ced5e6f'
    image_path = project_id + '/image_name'

    def get(self, url):
        auth = base64.b64encode('%s:%s' % ("infrabox", self.token,))
        headers = {'authorization': "Basic " + auth}
        return requests.get(url, headers=headers)

    def put(self, url):
        auth = base64.b64encode('%s:%s' % ("infrabox", self.token,))
        headers = {'authorization': "Basic " + auth}
        return requests.put(url, headers=headers)

    def post(self, url):
        auth = base64.b64encode('%s:%s' % ("infrabox", self.token,))
        headers = {'authorization': "Basic " + auth}
        return requests.post(url, headers=headers)

    def patch(self, url):
        auth = base64.b64encode('%s:%s' % ("infrabox", self.token,))
        headers = {'authorization': "Basic " + auth}
        return requests.patch(url, headers=headers)

    def delete(self, url):
        auth = base64.b64encode('%s:%s' % ("infrabox", self.token,))
        headers = {'authorization': "Basic " + auth}
        return requests.delete(url, headers=headers)

    def setUp(self):
        cur = conn.cursor()
        cur.execute('''INSERT INTO auth_token (token, description, project_id, scope_push, scope_pull)
                        VALUES(%s, 'test token', %s, true, true)''', (self.token, self.project_id,))
        cur.execute('''INSERT INTO project(name, type, id)
                        VALUES('test', 'upload', %s)''', (self.project_id,))
        cur.execute('''INSERT INTO collaborator(project_id, user_id)
                        VALUES(%s, %s)''', (self.project_id, self.user_id,))


    def tearDown(self):
        cur = conn.cursor()
        cur.execute('''DELETE FROM auth_token''')
        cur.execute('''DELETE FROM collaborator''')
        cur.execute('''DELETE FROM project''')

    # /v2/
    def test_v2(self):
        "GET /v2/ should be accessible to every authenticated user"
        r = self.get('http://docker-registry:8080/v2/')
        assert r.status_code == 200

    # /v2/_catalog
    def test_v2_catalog(self):
        "GET /v2/_catalog should not be accessible by anybody"
        r = self.get('http://docker-registry:8080/v2/_catalog')
        assert r.status_code == 401

    # /v2/<name>/tags/list
    def test_v2_project_tags_list_get(self):
        "GET /v2/<p>/tags/list should not be accessible by collaborators"
        r = self.get('http://docker-registry:8080/v2/%s/tags/list' % self.image_path)
        assert r.status_code == 401

    def test_v2_project_tags_list_get_2(self):
        "GET /v2/<p>/tags/list/ should not be accessible by collaborators"
        r = self.get('http://docker-registry:8080/v2/%s/tags/list/' % self.image_path)
        assert r.status_code == 401

    def test_v2_project_tags_list_get_foreign(self):
        "GET /v2/<p>/tags/list should not be accessible by foreign users"
        r = self.get('http://docker-registry:8080/v2/%s/tags/list' % self.foreign_project_id)
        assert r.status_code == 401

    def test_v2_project_tags_list_put(self):
        "PUT /v2/<p>/tags/list should NOT be accessible by collaborators"
        r = self.put('http://docker-registry:8080/v2/%s/tags/list' % self.image_path)
        assert r.status_code == 401

    def test_v2_project_tags_list_delete(self):
        "DELETE /v2/<p>/tags/list should NOT be accessible by collaborators"
        r = self.delete('http://docker-registry:8080/v2/%s/tags/list' % self.image_path)
        assert r.status_code == 401

    # /v2/<name>/manifests/<reference>
    def test_v2_project_manifests_reference_get(self):
        "GET /v2/<p>/manifests/<r> should be accessible by collaborators"
        r = self.get('http://docker-registry:8080/v2/%s/manifests/ref/' % self.image_path)
        assert r.status_code == 200

    def test_v2_project_manifests_reference_put(self):
        "PUT /v2/<p>/manifests/<r> should not be accessible by collaborators"
        r = self.put('http://docker-registry:8080/v2/%s/manifests/ref/' % self.image_path)
        assert r.status_code == 401

    def test_v2_project_manifests_reference_delete(self):
        "DELETE /v2/<p>/manifests/<r> should not be accessible by collaborators"
        r = self.delete('http://docker-registry:8080/v2/%s/manifests/ref/' % self.image_path)
        assert r.status_code == 401

    # /v2/<name>/blobs/<digest>
    def test_v2_project_blobs_digest_get(self):
        "GET /v2/<p>/blobs/<d> should be accessible by collaborators"
        r = self.get('http://docker-registry:8080/v2/%s/blobs/digest/' % self.image_path)
        assert r.status_code == 200

    def test_v2_project_blobs_digest_put(self):
        "PUT /v2/<p>/blobs/<d> should not be accessible by collaborators"
        r = self.put('http://docker-registry:8080/v2/%s/blobs/digest/' % self.image_path)
        assert r.status_code == 401

    def test_v2_project_blobs_digest_delete(self):
        "DELETE /v2/<p>/blobs/<d> should not be accessible by collaborators"
        r = self.delete('http://docker-registry:8080/v2/%s/blobs/digest/' % self.image_path)
        assert r.status_code == 401

    # /v2/<name>/blobs/upload/<uuid>
    def test_v2_project_blobs_upload_get(self):
        "GET /v2/<p>/blobs/upload/<uuid> should not be accessible by collaborators"
        r = self.get('http://docker-registry:8080/v2/%s/blobs/upload/uuid' % self.image_path)
        assert r.status_code == 200

    def test_v2_project_blobs_upload_put(self):
        "PUT /v2/<p>/blobs/upload/<uuid> should not be accessible by collaborators"
        r = self.put('http://docker-registry:8080/v2/%s/blobs/upload/uuid' % self.image_path)
        assert r.status_code == 401

    def test_v2_project_blobs_upload_delete(self):
        "DELETE /v2/<p>/blobs/upload/<uuid> should not be accessible by collaborators"
        r = self.delete('http://docker-registry:8080/v2/%s/blobs/upload/uuid' % self.image_path)
        assert r.status_code == 401

    def test_v2_project_blobs_upload_patch(self):
        "DELETE /v2/<p>/blobs/upload/<uuid> should not be accessible by collaborators"
        r = self.patch('http://docker-registry:8080/v2/%s/blobs/upload/uuid' % self.image_path)
        assert r.status_code == 401
