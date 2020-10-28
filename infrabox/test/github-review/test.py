# pylint: disable=attribute-defined-outside-init,relative-import
import unittest
import copy
import mock
import xmlrunner

from review import handle_job_update

class MockResponse(object):
    def __init__(self, status_code):
        self.status_code = status_code
        self.text = 'mock text'

class TestIt(unittest.TestCase):

    def setUp(self):
        self.event = {
            'job_id': 'bfdf1c99-ba5d-4cb9-a7f5-d574375d8187'
        }

        self.job_data = {
            'id': 'bfdf1c99-ba5d-4cb9-a7f5-d574375d8187',
            'state': 'running',
            'name': 'jobname',
            'project_id': 'afdf1c99-ba5d-4cb9-a7f5-d574375d8187',
            'build_id': 'cfdf1c99-ba5d-4cb9-a7f5-d574375d8187'
        }

        self.project_data = {
            'id': 'afdf1c99-ba5d-4cb9-a7f5-d574375d8187',
            'name': 'projectname',
            'type': 'github'
        }

        self.build_data = {
            'id': 'cfdf1c99-ba5d-4cb9-a7f5-d574375d8187',
            'build_number': 123,
            'restart_counter': 123,
            'commit_id': 'sha'
        }

        self.cluster_data = {
            'root_url': 'GITHUB_URL'
        }

        self.token_data = {
            'github_api_token': 'token'
        }

        self.commit_data = {
            'github_status_url': 'status_url'
        }

    @mock.patch('review.execute_sql')
    def test_job_not_found(self, execute_sql):
        execute_sql.return_value = []
        r = handle_job_update(None, self.event)
        self.assertFalse(r)

    @mock.patch('review.execute_sql')
    def test_project_not_found(self, execute_sql):
        sql_result = [[self.job_data], []]

        def side_effect(_1, _2, _3):
            return sql_result.pop(0)

        execute_sql.side_effect = side_effect
        r = handle_job_update(None, self.event)
        self.assertFalse(r)

    @mock.patch('review.execute_sql')
    def test_project_is_not_github(self, execute_sql):
        project_data = copy.deepcopy(self.project_data)
        project_data['type'] = 'gerrit'

        sql_result = [[self.job_data], []]

        def side_effect(_1, _2, _3):
            return sql_result.pop(0)

        execute_sql.side_effect = side_effect
        r = handle_job_update(None, self.event)
        self.assertFalse(r)

    @mock.patch('review.execute_sql')
    def test_build_not_found(self, execute_sql):
        sql_result = [[self.job_data], [self.project_data], []]

        def side_effect(_1, _2, _3):
            return sql_result.pop(0)

        execute_sql.side_effect = side_effect
        r = handle_job_update(None, self.event)
        self.assertFalse(r)

    @mock.patch('review.get_env')
    @mock.patch('review.execute_sql')
    def test_no_token_found(self, execute_sql, get_env):
        get_env.return_value = 'GITHUB_URL'
        execute_sql.return_value = []
        r = handle_job_update(None, self.event)
        self.assertFalse(r)

    @mock.patch('requests.post')
    @mock.patch('review.get_env')
    @mock.patch('review.execute_sql')
    def test_github_status_post_failed(self, execute_sql, get_env, requests_post):
        get_env.return_value = 'GITHUB_URL'
        requests_post.return_value = MockResponse(404)

        sql_result = [[self.job_data],
                      [self.project_data],
                      [self.build_data],
                      [self.token_data],
                      [self.commit_data],
                      [self.cluster_data]]

        def side_effect(_1, _2, _3):
            return sql_result.pop(0)

        execute_sql.side_effect = side_effect
        handle_job_update(None, self.event)

        requests_post.assert_called_with(
            'status_url',
            data='{"state": "pending", "target_url": "GITHUB_URL/dashboard/#/project/projectname/build/123/123/job/jobname", "description": "%s", "context": "Job: jobname"}' % ("project_id:%s job_id:%s" % (self.job_data['project_id'], self.job_data['id']) ),
            headers={'Authorization': 'token token', 'User-Agent': 'InfraBox'},
            timeout=10,
            verify=False)

    @mock.patch('requests.post')
    @mock.patch('review.get_env')
    @mock.patch('review.execute_sql')
    def run_github_status_post_succeeded(self, execute_sql, get_env, requests_post):
        job_data = copy.deepcopy(self.job_data)
        job_data['state'] = self.job_state
        get_env.return_value = 'GITHUB_URL'
        requests_post.return_value = MockResponse(201)

        sql_result = [[job_data],
                      [self.project_data],
                      [self.build_data],
                      [self.token_data],
                      [self.commit_data],
                      [self.cluster_data]]

        def side_effect(_1, _2, _3):
            return sql_result.pop(0)

        execute_sql.side_effect = side_effect
        handle_job_update(None, self.event)
        data = '{"state": "%s", "target_url": "GITHUB_URL/dashboard/#/project/projectname/build/123/123/job/jobname", "description": "%s", "context": "Job: jobname"}' % (self.expected_github_status, "project_id:%s job_id:%s" % (self.job_data['project_id'], self.job_data['id']))
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
