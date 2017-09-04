import os
import sys
import json
from unittest import TestCase
import requests
import psycopg2
import psycopg2.extensions

if 'INFRABOX_DATABASE_USER' not in os.environ:
    print "INFRABOX_DATABASE_USER not set"
    sys.exit(1)

if 'INFRABOX_DATABASE_PASSWORD' not in os.environ:
    print "INFRABOX_DATABASE_PASSWORD not set"
    sys.exit(1)

if 'INFRABOX_DATABASE_DB' not in os.environ:
    print "INFRABOX_DATABASE_DB not set"
    sys.exit(1)

if 'INFRABOX_DATABASE_HOST' not in os.environ:
    print "INFRABOX_DATABASE_HOST not set"
    sys.exit(1)

conn = psycopg2.connect(dbname=os.environ['INFRABOX_DATABASE_DB'],
                        user=os.environ['INFRABOX_DATABASE_USER'],
                        password=os.environ['INFRABOX_DATABASE_PASSWORD'],
                        host=os.environ['INFRABOX_DATABASE_HOST'],
                        port=os.environ['INFRABOX_DATABASE_PORT'])

conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

class Test(TestCase):
    job_id = '1514af82-3c4f-4bb5-b1da-a89a0ced5e6f'
    user_id = '2514af82-3c4f-4bb5-b1da-a89a0ced5e6b'
    build_id = '3514af82-3c4f-4bb5-b1da-a89a0ced5e6a'
    project_id = '4514af82-3c4f-4bb5-b1da-a89a0ced5e6f'
    source_upload_id = '5514af82-3c4f-4bb5-b1da-a89a0ced5e6f'

    def setUp(self):
        cur = conn.cursor()
        cur.execute('''DELETE FROM job''')
        cur.execute('''DELETE FROM auth_token''')
        cur.execute('''DELETE FROM collaborator''')
        cur.execute('''DELETE FROM project''')
        cur.execute('''DELETE FROM "user"''')
        cur.execute('''DELETE FROM source_upload''')
        cur.execute('''DELETE FROM build''')
        cur.execute('''DELETE FROM test_run''')
        cur.execute('''DELETE FROM job_stat''')
        cur.execute('''DELETE FROM measurement''')
        cur.execute('''DELETE FROM test''')
        cur.execute('''DELETE FROM job_markup''')
        cur.execute('''DELETE FROM user_quota''')

        cur.execute('''INSERT INTO job(id, state, start_date, build_id, type, dockerfile, name,
                            cpu, memory, project_id, dependencies, build_only,
                            keep, repo, base_path, deployment)
                        VALUES(%s, 'scheduled', now(), %s, 'run_project_container', 'Dockerfile',
                            'test', 1, 1024, %s, null, false, false, null, null,
                            '[{"type": "docker-registry", "username": "user", "password": {"$ref": "SECRET"}, "host": "host", "repository": "repo"}]')''',
                    (self.job_id, self.build_id, self.project_id))
        cur.execute('''INSERT INTO build(id, build_number, project_id, source_upload_id)
                        VALUES(%s, 1, %s, %s)''',
                    (self.build_id, self.project_id, self.source_upload_id))
        cur.execute('''INSERT INTO "user"(id, github_id, avatar_url, name,
                            email, github_api_token, username)
                        VALUES(%s, 1, 'avatar', 'name', 'email', 'token', 'login')''', (self.user_id,))
        cur.execute('''INSERT INTO project(name, type, id)
                        VALUES('test', 'upload', %s)''', (self.project_id,))
        cur.execute('''INSERT INTO collaborator(project_id, user_id, owner)
                        VALUES(%s, %s, true)''', (self.project_id, self.user_id,))
        cur.execute('''INSERT INTO source_upload(project_id, id, filename, filesize)
                        VALUES(%s, %s, 'filename', 123)''',
                    (self.project_id, self.source_upload_id))
        cur.execute('''INSERT INTO user_quota(user_id, max_concurrent_jobs, max_cpu_per_job,
                        max_memory_per_job, max_jobs_per_build)
                        VALUES(%s, 1, 1, 1024, 50)''',
                    (self.user_id,))

        cur.execute('''INSERT INTO secret (project_id, name, value)
                        VALUES(%s, 'SECRET', 'my secret')''',
                    (self.project_id,))

    def test_get_job(self):
        """GET: /job should return all the job data"""
        r = requests.get('http://api-server:5000/job')
        assert r.status_code == 200
        data = {
            "build": {
                "build_number": 1,
                "commit_id": None,
                "id": self.build_id,
                "source_upload_id": self.source_upload_id
            },
            "commit": {
                "branch": None,
                "tag": None
            },
            "deployments": [{
                "type": "docker-registry",
                "username": "user",
                "host": "host",
                "password": "my secret",
                "repository": "repo"
            }],
            "dependencies": [],
            "parents": [],
            "environment": {
                "INFRABOX_BUILD_NUMBER": "1",
                "INFRABOX_JOB_ID": "1514af82-3c4f-4bb5-b1da-a89a0ced5e6f",
                "TERM": "xterm-256color"
            },
            "job": {
                "base_path": None,
                "build_only": False,
                "build_arguments": None,
                "dockerfile": "Dockerfile",
                "repo": None,
                "id": "1514af82-3c4f-4bb5-b1da-a89a0ced5e6f",
                "keep": False,
                "cpu": 1,
                "memory": 1024,
                "name": "test",
                "type": "run_project_container",
                "state": "scheduled",
                "scan_container": False
            },
            "project": {
                "id": "4514af82-3c4f-4bb5-b1da-a89a0ced5e6f",
                "name": "test",
                "type": "upload"
            },
            "quota": {
                "max_concurrent_jobs": 1,
                "max_cpu_per_job": 1,
                "max_memory_per_job": 1024,
                "max_jobs_per_build": 50
            },
            "repository": {
                "private": False,
                "github_api_token": "token",
                "name": None,
                "owner": "login"
            },
            "source_upload": {
                "filename": "filename"
            }
        }
        result = r.json()
        data2 = json.dumps(data, indent=4, sort_keys=True)
        result2 = json.dumps(result, indent=4, sort_keys=True)

        print data2
        print result2

        self.assertEqual(data, result)

    def test_upload_test_result(self):
        """test empty json doc"""
        with open('/tmp/testresult.json', 'w+') as f:
            data = {}
            json.dump(data, f)

        with open('/tmp/testresult.json', 'r') as f:
            files = {"data": f}
            r = requests.post('http://api-server:5000/testresult', files=files)

            assert r.status_code == 400
            print r.text
            assert r.text == "#: property 'version' is required"

    def test_upload_test_result_2(self):
        """test invalid json data"""
        with open('/tmp/testresult.json', 'w+') as f:
            f.write("some data")

        with open('/tmp/testresult.json', 'r') as f:
            files = {"data": f}
            r = requests.post('http://api-server:5000/testresult', files=files)

            assert r.status_code == 404
            print r.text
            assert r.text == "Failed to parse json"

    def test_upload_test_result_3(self):
        """test almost valid json, but one wrong value"""
        with open('/tmp/testresult.json', 'w+') as f:
            json.dump({
                "version": 1,
                "tests": [{
                    "suite": "suite",
                    "name": "name",
                    "status": "ok",
                    "duration": "123",
                }]
            }, f)

        with open('/tmp/testresult.json', 'r') as f:
            files = {"data": f}
            r = requests.post('http://api-server:5000/testresult', files=files)

            assert r.status_code == 400
            print r.text
            assert r.text == "#tests[0].duration: must be a number"


    def test_upload_test_result_valid(self):
        """Test valid data"""
        with open('/tmp/testresult.json', 'w+') as f:
            json.dump({
                "version": 1,
                "tests": [{
                    "suite": "suite",
                    "name": "name",
                    "status": "ok",
                    "duration": 123,
                }]
            }, f)

        with open('/tmp/testresult.json', 'r') as f:
            files = {"data": f}
            r = requests.post('http://api-server:5000/testresult', files=files)

            assert r.status_code == 200
            assert r.text == ""

    def test_upload_markdown(self):
        """Test valid data"""
        with open('/tmp/test.md', 'w+') as f:
            f.write("# Header")

        with open('/tmp/test.md', 'r') as f:
            files = {"data": f}
            r = requests.post('http://api-server:5000/markdown', files=files)

            assert r.status_code == 200
            assert r.text == ""
