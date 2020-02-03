import unittest
import json

from temp_tools import TestClient

class ApiTestTemplate(unittest.TestCase):
    # TODO optimize setup for each test

    def setUp(self):
        TestClient.execute('TRUNCATE "user"')
        TestClient.execute('TRUNCATE project')
        TestClient.execute('TRUNCATE collaborator')
        TestClient.execute('TRUNCATE repository')
        TestClient.execute('TRUNCATE commit')
        TestClient.execute('TRUNCATE build')
        TestClient.execute('TRUNCATE console')
        TestClient.execute('TRUNCATE job')
        TestClient.execute('TRUNCATE job_markup')
        TestClient.execute('TRUNCATE job_badge')
        TestClient.execute('TRUNCATE source_upload')
        TestClient.execute('TRUNCATE secret')
        TestClient.execute('TRUNCATE cluster')
        TestClient.execute('TRUNCATE auth_token')

        self.project_id = '1514af82-3c4f-4bb5-b1da-a89a0ced5e6f'
        self.project_id_github = '1614af82-3c4f-4bb5-b1da-a89a0ced5e6f'
        self.project_id_no_collab = '1714af82-3c4f-4bb5-b1da-a89a0ced5e6f'
        self.user_id = '2514af82-3c4f-4bb5-b1da-a89a0ced5e6f'
        self.repo_id = '3514af82-3c4f-4bb5-b1da-a89a0ced5e6f'
        self.build_id = '4514af82-3c4f-4bb5-b1da-a89a0ced5e6f'
        self.job_id = '1454af82-4c4f-4bb5-b1da-a54a0ced5e6f'
        self.job_id_2 = '1554af82-4c4f-4bb5-b1da-a54a0ced5e6f'
        self.job_id_running = '1554af82-4c4f-4bb5-b1da-a42a0ced5e6f'
        self.token_id = '2bbc6c34-11dd-448c-a678-7209a071b12a'
        self.job_name = 'test_job_name1'
        self.sha = 'd670460b4b4aece5915caf5c68d12f560a9fe3e4'
        self.author_name = 'author_name1'
        self.author_email = 'author@email.1'
        self.source_upload_id = '1423af82-3c4f-5bb5-b1da-a23a0ced5e6f'
        self.user_github_id = 24122

        self.job_headers = TestClient.get_job_authorization(self.job_id)

        TestClient.execute("""
                INSERT INTO cluster (name, active, labels, root_url, nodes, cpu_capacity, memory_capacity)
                VALUES ('master', true, '{master,default}', 'http://localhost:8080', 1, 10, 10000);
            """)

        TestClient.execute("""
                INSERT INTO collaborator (user_id, project_id, role)
                VALUES (%s, %s, 'Owner');
            """, [self.user_id, self.project_id])

        TestClient.execute("""
                INSERT INTO "user" (id, github_id, username, avatar_url)
                VALUES (%s, %s, %s, 'url');
            """, [self.user_id, self.user_github_id, self.author_name])

        TestClient.execute("""
                INSERT INTO project(id, name, type)
                VALUES (%s, 'testproject', 'upload');
            """, [self.project_id])

        TestClient.execute("""
                INSERT INTO project(id, name, type)
                VALUES (%s, 'testproject_archive_github', 'github');
            """, [self.project_id_github])

        TestClient.execute("""
                INSERT INTO project(id, name, type)
                VALUES (%s, 'testproject_archive_no_collab', 'upload');
            """, [self.project_id_no_collab])

        TestClient.execute('''
            INSERT INTO auth_token (id, description, scope_push, scope_pull, project_id)
            VALUES (%s, 'PToken', True, True, %s)
        ''', [self.token_id, self.project_id])

        TestClient.execute("""
                INSERT INTO repository(id, name, html_url, clone_url, github_id, project_id, private)
                VALUES (%s, 'testrepo', 'url', 'clone_url', 0, %s, true);
            """, [self.repo_id, self.project_id])

        definition = {
            'build_only': True,
            'resources': {
                'limits': {
                    'cpu': 1,
                    'memory': 512
                }
            }
        }

        TestClient.execute("""
                INSERT INTO job (id, state, build_id, type, name, project_id,
                                dockerfile, cluster_name, definition)
                VALUES (%s, 'queued', %s, 'create_job_matrix',
                        %s, %s, '', 'master', %s);
            """, [self.job_id_2, self.build_id, "Create Jobs", self.project_id, json.dumps(definition)])

        TestClient.execute("""
                INSERT INTO job (id, state, build_id, type, name, project_id,
                                dockerfile, cluster_name, definition)
                VALUES (%s, 'queued', %s, 'run_docker_compose',
                        %s, %s, '', 'master', %s);
            """, [self.job_id, self.build_id, self.job_name, self.project_id, json.dumps(definition)])

        definition_running = {
            'build_only': True,
            'name': 'running_job',
            'resources': {
                'limits': {
                    'cpu': 1,
                    'memory': 512
                }
            }
        }
        TestClient.execute("""
                INSERT INTO job (id, state, build_id, type, name, project_id,
                                dockerfile, cluster_name, definition)
                VALUES (%s, 'running', %s, 'run_docker_compose',
                        'running_job', %s, '', 'master', %s);
            """, [self.job_id_running, self.build_id, self.project_id, json.dumps(definition_running)])

        TestClient.execute("""
                INSERT INTO build (id, project_id, build_number, commit_id, source_upload_id)
                VALUES (%s, %s, 1, %s, %s);
            """, [self.build_id, self.project_id, self.sha, self.source_upload_id])

        TestClient.execute("""
                INSERT INTO commit (id, repository_id, "timestamp", project_id, author_name,
                                    author_email, committer_name, committer_email, url, branch)
                VALUES (%s, %s, now(), %s, %s, %s, %s, %s, 'url1', 'branch1');
            """, [self.sha, self.repo_id, self.project_id,
                  self.author_name, self.author_email, self.author_name, self.author_email])

        TestClient.opa_push()


