from os import remove

import json

import psycopg2

import server


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

    @staticmethod
    def get(url, headers):  # pragma: no cover

        r = TestClient.app.get(url, headers=headers)

        if r.mimetype == 'application/json':
            j = json.loads(r.data)
            return j

        return r

    @staticmethod
    def delete(url, headers):  # pragma: no cover

        r = TestClient.app.delete(url, headers=headers)

        if r.mimetype == 'application/json':
            j = json.loads(r.data)
            return j

        return r

    @staticmethod
    def post(url, data, headers, content_type='application/json'): # pragma: no cover
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
