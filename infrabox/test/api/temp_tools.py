from os import remove

import json

import psycopg2

from api import server
from pyinfraboxutils.db import connect_db
from pyinfraboxutils.token import encode_user_token, encode_project_token, encode_job_token
from pyinfraboxutils.ibopa import opa_push_all


class TestUtils:

    current_test_counter = 0

    @staticmethod
    def get_stream_file_size(result_stream):
        file_size = 0

        TestUtils.current_test_counter += 1
        file_name = "%s.tmp_test_file" % TestUtils.current_test_counter

        with open(file_name, "wb") as receive_cache:
            receive_cache.write(result_stream)
            file_size = receive_cache.tell()
        remove(file_name)

        return file_size


class TestClient:

    app = server.app.test_client()
    server.app.testing = True
    conn = connect_db()

    @staticmethod
    def execute(stmt, args=None):
        cur = TestClient.conn.cursor()
        cur.execute(stmt, args)
        cur.close()
        TestClient.conn.commit()

    @staticmethod
    def execute_many(stmt, args=None):
        cur = TestClient.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(stmt, args)
        d = cur.fetchall()
        cur.close()
        TestClient.conn.commit()
        return d

    @staticmethod
    def execute_one(stmt, args=None):
        return TestClient.execute_many(stmt, args)[0]

    @staticmethod
    def get_user_authorization(user_id): # pragma: no cover
        token = encode_user_token(user_id)
        h = {'Authorization': 'token %s' % token}
        return h

    @staticmethod
    def get_job_authorization(job_id): # pragma: no cover
        job_api_token = encode_job_token(job_id)
        h = {'Authorization': 'token %s' % job_api_token}
        return h

    @staticmethod
    def get_project_authorization(token_id, project_id):  # pragma: no cover
        project_token = encode_project_token(token_id, project_id, 'myproject')
        h = {'Authorization': 'token %s' % project_token}
        return h

    @staticmethod
    def get(url, headers):  # pragma: no cover

        if not headers:
            return

        r = TestClient.app.get(url, headers=headers)

        if r.mimetype == 'application/json':
            j = json.loads(r.data)
            return j

        return r

    @staticmethod
    def delete(url, headers):  # pragma: no cover

        if not headers:
            return

        r = TestClient.app.delete(url, headers=headers)

        if r.mimetype == 'application/json':
            j = json.loads(r.data)
            return j

        return r

    @staticmethod
    def post(url, data, headers, content_type='application/json'): # pragma: no cover
        if not headers:
            return

        if content_type == 'application/json':
            data = json.dumps(data)

        r = TestClient.app.post(url,
                          data=data,
                          headers=headers,
                          content_type=content_type)

        if r.mimetype == 'application/json':
            j = json.loads(r.data)
            return j

        return r


    @staticmethod
    def opa_push():
        opa_push_all()