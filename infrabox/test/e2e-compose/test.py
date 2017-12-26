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

    def run_it(self, cwd):
        command = ['infrabox', 'push', '--show-console']
        process = subprocess.Popen(command, shell=False,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   cwd=cwd, universal_newlines=True)

        # Poll process for new output until finished
        msg = ""
        while True:
            line = process.stdout.readline()
            if not line:
                break

            line = line.rstrip()
            msg += line
            print line

        process.wait()

        exitCode = process.returncode
        print "Test exited with %s" % exitCode

        if exitCode != 0:
            raise Exception(msg)

    def test_docker_job(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_job')

    def test_docker_compose_job(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_compose_job')

    def test_failed_job(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/failed_job')

    def test_input_output(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_input_output')

    def test_secure_env(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_secure_env')

    def test_insecure_env(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_insecure_env')


if __name__ == '__main__':
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
