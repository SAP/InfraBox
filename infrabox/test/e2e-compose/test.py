import unittest
import os
import subprocess
import time
import xmlrunner
import requests

from pyinfraboxutils.db import connect_db
from pyinfraboxutils.token import encode_project_token

class Test(unittest.TestCase):
    job_id = '1514af82-3c4f-4bb5-b1da-a89a0ced5e6f'
    user_id = '2514af82-3c4f-4bb5-b1da-a89a0ced5e6b'
    build_id = '3514af82-3c4f-4bb5-b1da-a89a0ced5e6a'
    project_id = '4514af82-3c4f-4bb5-b1da-a89a0ced5e6f'
    token_id = '5514af82-3c4f-4bb5-b1da-a89a0ced5e6f'

    def setUp(self):
        conn = connect_db()
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
        cur.execute('''INSERT INTO "user"(id, github_id, avatar_url, name,
                            email, github_api_token, username)
                        VALUES(%s, 1, 'avatar', 'name', 'email', 'token', 'login')''', (self.user_id,))
        cur.execute('''INSERT INTO project(name, type, id)
                        VALUES('test', 'upload', %s)''', (self.project_id,))
        cur.execute('''INSERT INTO collaborator(project_id, user_id, owner)
                        VALUES(%s, %s, true)''', (self.project_id, self.user_id,))
        cur.execute('''INSERT INTO auth_token(project_id, id, description, scope_push, scope_pull)
                        VALUES(%s, %s, 'asd', true, true)''', (self.project_id, self.token_id,))
        conn.commit()

        os.environ['INFRABOX_CLI_TOKEN'] = encode_project_token(self.token_id, self.project_id)
        os.environ['INFRABOX_API_URL'] = 'http://nginx-ingress/api'

    def expect_message(self, output, message):
        if not message:
            return

        self.assertIn(message, output)

    def run_it(self, cwd, expect_message):
        command = ['infrabox', 'push', '--show-console']
        try:
            output = subprocess.check_output(command, cwd=cwd)
            self.expect_message(output, expect_message)
        except subprocess.CalledProcessError as e:
            self.expect_message(e.output, expect_message)

    def test_docker_job(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_job',
                    "Job test finished successfully")

    def test_docker_compose_job(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_compose_job',
                    "Job test finished successfully")

    def test_failed_job(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/failed_job',
                    "Job test failed with 'failure'")

    def test_input_output(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_input_output',
                    "Job test finished successfully")

    def test_secure_env(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_secure_env',
                    "Job test finished successfully")

    def test_insecure_env(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_insecure_env',
                    "Job test finished successfully")

def main():
    while True:
        time.sleep(1)
        try:
            r = requests.get('http://nginx-ingress')

            if r.status_code == 200:
                break
        except:
            pass
        print "Server not yet ready"

    connect_db() # Wait for DB

    with open('results.xml', 'wb') as output:
        unittest.main(testRunner=xmlrunner.XMLTestRunner(output=output))

if __name__ == '__main__':
    main()
