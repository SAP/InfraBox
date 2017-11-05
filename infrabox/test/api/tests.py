import uuid
import json
import os
import unittest
import xmlrunner

import psycopg2
import psycopg2.extensions
import requests

POSTGRES_URL = "postgres://postgres:postgres@postgres/postgres"
conn = psycopg2.connect(POSTGRES_URL)
conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
api_url = "http://github-trigger:8080/github/hook"

class TestGithubHook(unittest.TestCase):
    def get_file(self, p):
        p = os.path.join("test", p)
        with open(p) as f:
            return json.load(f)

    def test_no_github_event_header(self):
        r = requests.post(api_url, json={})
        res = r.json()
        print res
        assert r.status_code == 400
        assert res['message'] == "X-Github-Event not set"

    def test_no_hub_signature(self):
        h = {"X-Github-Event": "pull_request"}
        r = requests.post(api_url, json={}, headers=h)
        res = r.json()
        print res
        assert r.status_code == 400
        assert res['message'] == "X-Hub-Signature not set"

    def get_headers(self, event):
        h = {
            "content-type": "application/json",
            "X-Github-Event": event,
            "X-Hub-Signature": "sha1=somehex"
        }
        return h

    def disabled_test_pr_repo_does_not_exist(self):
        self.execute("""DELETE FROM repository""")

        pr = self.get_file("pr_open.json")
        r = requests.post(api_url, json=pr, headers=self.get_headers("pull_request"))
        res = r.json()
        print  res
        self.assertEqual(r.status_code, 404)
        self.assertEqual(res['message'], "Not Found")

    def execute(self, stmt, args=None):
        cur = conn.cursor()
        cur.execute(stmt, args)
        cur.close()

    def setup(self):
        project_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())

        self.execute("SELECT truncate_tables('postgres')")

        self.execute("""
            INSERT INTO repository (name, html_url, clone_url, github_id, project_id, private)
            VALUES ('repo', 'url', 'clone', 97029923, %s, true);
        """, (project_id, ))

        self.execute("""
            INSERT INTO collaborator (user_id, project_id, owner)
            VALUES (%s, %s, true);
        """, (user_id, project_id))

        self.execute("""
            INSERT INTO "user" (id, github_id, username,
                avatar_url)
            VALUES (%s, 1, 'testuser', 'url');
        """, (user_id,))

        self.execute("""
            INSERT INTO project(id, name, type)
            VALUES (%s, 'testproject', 'test');
        """, (project_id,))

        self.execute("""
            INSERT INTO secret (project_id, name, value)
            VALUES (%s, 'OTHER', 'value');
        """, (project_id,))

if __name__ == '__main__':
    with open('results.xml', 'wb') as output:
        unittest.main(testRunner=xmlrunner.XMLTestRunner(output=output))
