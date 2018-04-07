import unittest
import os
import subprocess
import time
import json
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
        cur.execute('''INSERT INTO secret(project_id, name, value)
                        VALUES(%s, 'SECRET_ENV', 'hello world')''', (self.project_id,))
        conn.commit()

        os.environ['INFRABOX_CLI_TOKEN'] = encode_project_token(self.token_id, self.project_id)

        ## TODO: docker: testresult
        ## TODO: docker: badge
        ## TODO: docker: markup
        ## TODO: docker: caching
        ## TODO: compose: caching
        ## TODO: compose: insecure environment vars
        ## TODO: compose: secure environment vars
        ## TODO: compose: output/input
        ## TODO: compose: testresult
        ## TODO: compose: badge
        ## TODO: compose: markup

    def expect_job(self, job_name, state='finished', message=None, parents=None, dockerfile=None):
        root_url = os.environ['INFRABOX_ROOT_URL']
        headers = {'Authorization': 'bearer ' + os.environ['INFRABOX_CLI_TOKEN']}
        url = '%s/api/v1/projects/%s/builds/' % (root_url, self.project_id)
        result = requests.get(url, headers=headers).json()
        build = result[0]
        url = '%s/api/v1/projects/%s/builds/%s/jobs/' % (root_url, self.project_id, build['id'])
        jobs = requests.get(url, headers=headers).json()

        for j in jobs:
            data = json.dumps(j, indent=4)
            if j['name'] != job_name:
                continue

            self.assertEqual(j['state'], state, data)

            if message:
                self.assertEqual(j['message'], message, data)

            if dockerfile:
                self.assertEqual(j['docker_file'], dockerfile, data)

            if parents:
                actual_parents = {}
                for p in j.get('depends_on', []):
                    actual_parents[p['job']] = p

                for p in parents:
                    self.assertTrue(p in actual_parents, data)

            return

        data = json.dumps(jobs, indent=4)
        raise Exception('Job "%s" not found in: %s' % (job_name, data))


    def run_it(self, cwd):
        command = ['infrabox', 'push', '--show-console']
        output = None
        try:
            output = subprocess.check_output(command, cwd=cwd)
        except subprocess.CalledProcessError as e:
            output = e.output

        print output

    def test_docker_job(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_job')
        self.expect_job('test')

    def test_docker_multiple_jobs(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_multiple_jobs')
        self.expect_job('test-1', parents=['Create Jobs'])
        self.expect_job('test-2', parents=['Create Jobs'])
        self.expect_job('test-3', parents=['Create Jobs'])
        self.expect_job('test-4', parents=['test-1', 'test-2'])
        self.expect_job('test-5', parents=['test-2', 'test-3'])

    def test_workflow_nested(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/workflow_nested')
        self.expect_job('flow', parents=['flow/sub-2', 'flow/sub-3'])
        self.expect_job('flow/sub-1', parents=['Create Jobs'], dockerfile='Dockerfile_flow')
        self.expect_job('flow/sub-2', parents=['flow/sub-2/nested-2', 'flow/sub-2/nested-3'])

        self.expect_job('flow/sub-2/nested-1',
                        parents=['flow/sub-1'],
                        dockerfile='Dockerfile_nested')
        self.expect_job('flow/sub-2/nested-2',
                        parents=['flow/sub-2/nested-1'],
                        dockerfile='Dockerfile_nested')
        self.expect_job('flow/sub-2/nested-3',
                        parents=['flow/sub-2/nested-1'],
                        dockerfile='Dockerfile_nested')
        self.expect_job('flow/sub-3',
                        parents=['flow/sub-1'],
                        dockerfile='Dockerfile_flow')


    def test_docker_compose_job(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_compose_job')
        self.expect_job('test')

    def test_docker_job_archive(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_job_archive')
        self.expect_job('test')

    def test_docker_compose_invalid_compose_file(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_compose_invalid_compose_file')
        self.expect_job('Create Jobs',
                        state='failure',
                        message='/tmp/infrabox-compose/repo/docker-compose.yml: version not found')

    def test_failed_job(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/failed_job')
        self.expect_job('test', state='failure')

    def test_malicious_job(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/malicious_job')
        self.expect_job('test')

    def test_workflow_recursive(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/workflow_recursive')
        self.expect_job('Create Jobs', state='failure', message='Recursive include detected')

    def test_workflow_simple_job(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/workflow_simple_job')
        self.expect_job('flow', parents=['flow/test-sub'])
        self.expect_job('flow/test-sub', parents=['Create Jobs'])

    def test_image_input_output(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_image_input_output')
        self.expect_job('consumer')

    def test_input_output(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_input_output')
        self.expect_job('consumer')

    def test_infrabox_context(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/infrabox_context')
        self.expect_job('root')
        self.expect_job('sub1')
        self.expect_job('sub1/sub1')

    def test_secure_env(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_secure_env')
        self.expect_job('test')

    def test_secure_env_not_found(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_secure_env_not_found')
        self.expect_job('Create Jobs', state='failure', message="Secret 'UNKNOWN_SECRET' not found")

    def test_insecure_env(self):
        self.run_it('/infrabox/context/infrabox/test/e2e/tests/docker_insecure_env')
        self.expect_job('test')

def main():
    root_url = os.environ['INFRABOX_ROOT_URL']

    print "ROOT_URL: %s" % root_url
    while True:
        time.sleep(1)
        try:
            r = requests.get(root_url)

            if r.status_code in (200, 404):
                break

            print r.text
        except:
            pass
        print "Server not yet ready"

    connect_db() # Wait for DB

    with open('results.xml', 'wb') as output:
        unittest.main(testRunner=xmlrunner.XMLTestRunner(output=output))

if __name__ == '__main__':
    main()
