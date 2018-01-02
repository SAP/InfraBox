import json
import os
import uuid
import shutil
import subprocess
from distutils.dir_util import copy_tree

import psycopg2
import psycopg2.extensions

from job import RunJob
from infrabox_job.process import ApiConsole

from pyinfraboxutils.token import encode_job_token

POSTGRES_URL = "postgres://postgres:postgres@postgres/postgres"

class TestCreateJobs(object):
    def __init__(self):
        self.conn = psycopg2.connect(POSTGRES_URL)
        self.conn.set_isolation_level(
            psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        self.job_id = "5df0e731-6040-46a9-8540-f1bb7935d2bd"
        subprocess.check_call(['git', 'config', '--global', 'user.email', 'you@example.com'])
        subprocess.check_call(['git', 'config', '--global', 'user.name', 'name'])

        self.token = encode_job_token(self.job_id)
        os.environ['INFRABOX_JOB_TOKEN'] = self.token

    def execute(self, stmt, args=None):
        cur = self.conn.cursor()
        cur.execute(stmt, args)
        cur.close()

    def test_deployment(self):
        path = '/project/infrabox/test/create-jobs/test/test-deployment'
        expect = (
            ('test-server', 'Dockerfile', ['Create Jobs'], [{
                'username': 'myuser',
                'host': 'myhost',
                'password': {
                    '$secret': 'MY_SECRET'
                },
                'type': 'docker-registry',
                'repository': 'repo'
            }, {
                'host': 'myhost',
                'type': 'docker-registry',
                'repository': 'repo'
            }]),
        )
        self.run(path, expect, with_deployment=True)

    def test_dependency_conditions(self):
        path = '/project/infrabox/test/create-jobs/test/test-dependency-conditions'
        expect = (
            ('consumer1', 'Dockerfile_consumer1', ['producer']),
            ('consumer2', 'Dockerfile_consumer2', ['producer']),
            ('consumer3', 'Dockerfile_consumer3', ['producer']),
            ('producer', 'Dockerfile_producer', ['Create Jobs']),
        )
        self.run(path, expect)


    def test_one_git_job(self):
        path = '/project/infrabox/test/create-jobs/test/test-one-git-job'
        gp = os.path.join(path, 'external_git')
        subprocess.check_call(['git', 'init'], cwd=gp)
        subprocess.check_call(['git', 'add', '.'], cwd=gp)
        subprocess.check_call(['git', 'commit', '-m', '"asd"'], cwd=gp)
        expect = (
            ('external', None, ['external/test-server'], None),
            ('external/test-server', 'Dockerfile_external',
             ['Create Jobs'],
             {
                 "commit": "master",
                 "clone_url": "/project/infrabox/test/create-jobs/test/test-one-git-job/external_git/",
                 "clone_all": False
             }),
        )
        self.run(path, expect, with_external_git_id=True)

    def test_one_git_job_env(self):
        path = '/project/infrabox/test/create-jobs/test/test-one-git-job-env'
        gp = os.path.join(path, 'external_git')
        subprocess.check_call(['git', 'init'], cwd=gp)
        subprocess.check_call(['git', 'add', '.'], cwd=gp)
        subprocess.check_call(['git', 'commit', '-m', '"asd"'], cwd=gp)
        expect = (
            ('external', None, ['external/test-server'], None, None, None),
            ('external/test-server', 'Dockerfile_external',
             ['Create Jobs'],
             {
                 "commit": "master",
                 "clone_url": "/project/infrabox/test/create-jobs/test/test-one-git-job-env/external_git/",
                 "clone_all": False
             },
             {"ENV_VAR": "OUTER_VALUE", "ANOTHER": "VALUE"}, None),
        )
        self.run(path, expect, with_external_git_id=True, with_environment=True)


    def test_git_with_workflow(self):
        path = '/project/infrabox/test/create-jobs/test/test-git-with-workflow'
        gp = os.path.join(path, 'external_git')
        subprocess.check_call(['git', 'init'], cwd=gp)
        subprocess.check_call(['git', 'add', '.'], cwd=gp)
        subprocess.check_call(['git', 'commit', '-m', '"asd"'], cwd=gp)
        expect = (
            ('external', None, ['external/flow'], None),
            ('external/flow', None, ['external/flow/test-server'], None),
            ('external/flow/test-server', 'flow/Dockerfile_flow',
             ['Create Jobs'],
             {
                 "commit": "master",
                 "clone_url": "/project/infrabox/test/create-jobs/test/test-git-with-workflow/external_git/",
                 "clone_all": False
             }),
        )
        self.run(path, expect, with_external_git_id=True)



    def expect(self, expect, with_external_git_id=False, with_base_path=False, with_environment=False,
               with_deployment=False):
        cur = self.conn.cursor()

        additional_cols = ""

        if with_external_git_id:
            additional_cols += ", repo"

        if with_base_path:
            additional_cols += ", base_path"

        if with_environment:
            additional_cols += ", env_var, env_var_ref"

        if with_deployment:
            additional_cols += ", deployment"

        cur.execute("""
	SELECT 	outer_job.name, outer_job.dockerfile,
		deps %s
	FROM job outer_job
	LEFT JOIN LATERAL (
		SELECT ARRAY(SELECT name FROM job j
		INNER JOIN (
                        SELECT (p->>'job-id')::uuid as id
                        FROM job, jsonb_array_elements(job.dependencies) p
			WHERE job.id = outer_job.id
		) deps
		ON j.id = deps.id
		ORDER BY name) deps FROM  job  where id = outer_job.id
	) e ON TRUE
	WHERE name != 'Create Jobs'
	ORDER BY name
        """ % additional_cols)
        rows = cur.fetchall()
        cur.close()

        result = []
        for r in rows:
            result.append(list(r))

        if len(expect) != len(result):
            print "Result size does not match"
            print "Expect: %s" % json.dumps(expect, indent=4)
            print "Actual: %s" % json.dumps(result, indent=4)
            raise Exception("Result size does not match")

        for x in xrange(0, len(expect)):
            act = result[x]
            exp = expect[x]

            for y in xrange(0, len(act)):
                if act[y] != exp[y]:
                    print "Result does not match in line %s" % x
                    print "Expect value: %s" % json.dumps(exp[y], indent=4)
                    print "Actual value: %s" % json.dumps(act[y], indent=4)

                    print "Expect: %s" % json.dumps(expect, indent=4)
                    print "Actual: %s" % json.dumps(result, indent=4)

                    raise Exception("Result does not match")


    def run(self, path, expect, with_external_git_id=False, with_base_path=False, with_environment=False,
            with_deployment=False):
        if os.path.exists('/repo/.infrabox'):
            shutil.rmtree('/repo/.infrabox')

        copy_tree(path, '/repo')

        console = ApiConsole()
        job = RunJob(console)
        job.main()

        self.expect(expect,
                    with_external_git_id=with_external_git_id,
                    with_base_path=with_base_path,
                    with_environment=with_environment,
                    with_deployment=with_deployment)

    def setup(self):
        build_id = str(uuid.uuid4())
        project_id = str(uuid.uuid4())
        source_upload_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())

        self.execute("SELECT truncate_tables('postgres')")

        self.execute("""
            INSERT INTO job (id, state, build_id, type, name,
                cpu, memory, project_id, build_only)
            VALUES(%s, 'scheduled', %s, 'create_job_matrix', 'Create Jobs',
                1, 1024, %s, false);
        """, (self.job_id, build_id, project_id))

        self.execute("""
            INSERT INTO build (id, build_number, project_id,
                source_upload_id)
            VALUES (%s, 1, %s, %s);
        """, (build_id, project_id, source_upload_id))

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

        self.execute("""
            INSERT INTO secret (project_id, name, value)
            VALUES (%s, 'MY_SECRET', 'my secret');
        """, (project_id,))
