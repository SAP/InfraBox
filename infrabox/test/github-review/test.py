# pylint: disable=attribute-defined-outside-init,relative-import
import unittest
import mock
import xmlrunner

from review import handle_job_update

class MockResponse(object):
    def __init__(self, status_code):
        self.status_code = status_code
        self.text = 'mock text'

class TestIt(unittest.TestCase):

    def setUp(self):
        self.update = {
            'data': {
                'project': {
                    'type': 'github',
                    'id': 'projectid',
                    'name': 'projectname'
                },
                'job': {
                    'state': 'scheduled',
                    'id': 'jobid',
                    'name': 'jobname',
                },
                'commit': {
                    'id': 'commitid',
                },
                'build': {
                    'id': 'buildid',
                    'build_number': 123,
                    'restart_counter': 123
                }
            }
        }


    def test_gerrit_update(self):
        update = {
            'data': {
                'project': {
                    'type': 'gerrit'
                }
            }
        }

        handle_job_update(None, update)

    @mock.patch('review.get_env')
    @mock.patch('review.execute_sql')
    def test_no_token_found(self, execute_sql, get_env):
        get_env.return_value = 'GITHUB_URL'
        execute_sql.return_value = []
        handle_job_update(None, self.update)

    @mock.patch('requests.post')
    @mock.patch('review.get_env')
    @mock.patch('review.execute_sql')
    def test_github_status_post_failed(self, execute_sql, get_env, requests_post):
        get_env.return_value = 'GITHUB_URL'
        requests_post.return_value = MockResponse(404)

        sql_result = [[['status_url']], [['token']]]

        def side_effect(_1, _2, _3):
            return sql_result.pop()

        execute_sql.side_effect = side_effect
        handle_job_update(None, self.update)

        requests_post.assert_called_with(
            'status_url',
            data='{"state": "pending", "target_url": "GITHUB_URL/dashboard/#/project/projectname/build/123/123/job/jobname", "description": "InfraBox", "context": "Job: jobname"}',
            headers={'Authorization': 'token token', 'User-Agent': 'InfraBox'},
            timeout=10,
            verify=False)

    @mock.patch('requests.post')
    @mock.patch('review.get_env')
    @mock.patch('review.execute_sql')
    def run_github_status_post_succeeded(self, execute_sql, get_env, requests_post):
        self.update['data']['job']['state'] = self.job_state
        get_env.return_value = 'GITHUB_URL'
        requests_post.return_value = MockResponse(201)

        sql_result = [[['status_url']], [['token']]]

        def side_effect(_1, _2, _3):
            return sql_result.pop()

        execute_sql.side_effect = side_effect
        handle_job_update(None, self.update)
        data = '{"state": "%s", "target_url": "GITHUB_URL/dashboard/#/project/projectname/build/123/123/job/jobname", "description": "InfraBox", "context": "Job: jobname"}' % self.expected_github_status
        requests_post.assert_called_with(
            'status_url',
            data=data,
            headers={'Authorization': 'token token',
                     'User-Agent': 'InfraBox'},
            timeout=10,
            verify=False)

    def test_status_error(self):
        # pylint: disable=no-value-for-parameter
        self.job_state = 'error'
        self.expected_github_status = 'error'
        self.run_github_status_post_succeeded()

    def test_status_success(self):
        # pylint: disable=no-value-for-parameter
        self.job_state = 'finished'
        self.expected_github_status = 'success'
        self.run_github_status_post_succeeded()

    def test_status_pending(self):
        for s in ('scheduled', 'running', 'queued'):
            # pylint: disable=no-value-for-parameter
            self.job_state = s
            self.expected_github_status = 'pending'
            self.run_github_status_post_succeeded()

    def test_status_failure(self):
        for s in ('failure', 'skipped', 'killed'):
            # pylint: disable=no-value-for-parameter
            self.job_state = s
            self.expected_github_status = 'failure'
            self.run_github_status_post_succeeded()


if __name__ == '__main__':
    with open('results.xml', 'wb') as output:
        unittest.main(testRunner=xmlrunner.XMLTestRunner(output=output))
