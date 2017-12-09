import unittest
import mock
from boddle import boddle
import xmlrunner

from api import get_commit, execute_api

class MockResponse(object):
    def __init__(self, status_code, json_result=None):
        self.status_code = status_code
        self.json_result = json_result

    def json(self):
        if not self.json_result:
            return None

        return self.json_result.pop(0)

class TestIt(unittest.TestCase):
    @mock.patch('api.get_env')
    @mock.patch('requests.get')
    def test_execute_api(self, request_get, get_env):
        get_env.return_value = ''
        execute_api('url', 'token')
        request_get.assert_called_with('url', {
            "Authorization": "token token",
            "User-Agent": "InfraBox"
        }, verify=False)


    def test_get_commit_owner_not_set(self):
        with boddle():
            self.assertEqual(get_commit(), {'message': 'owner not set'})

    def test_get_commit_token_not_set(self):
        with boddle(params={'owner': 'myowner'}):
            self.assertEqual(get_commit(), {'message': 'token not set'})

    def test_get_commit_repo_not_set(self):
        with boddle(params={'owner': 'myowner', 'token': 'mytoken'}):
            self.assertEqual(get_commit(), {'message': 'repo not set'})

    def test_get_commit_branch_and_sha_not_set(self):
        with boddle(params={'owner': 'myowner', 'token': 'mytoken', 'repo': 'myrepo'}):
            self.assertEqual(get_commit(), {'message': 'either branch or sha must be set'})

    @mock.patch('api.execute_api')
    def test_get_commit_for_branch_failed_execute(self, mocked):
        with boddle(params={'owner': 'myowner', 'token': 'mytoken', 'repo': 'myrepo', 'branch': 'mybranch'}):
            mocked.return_value = MockResponse(404)
            self.assertEqual(get_commit(), {'message': 'internal server error'})

    @mock.patch('api.execute_api')
    def test_get_commit_for_branch(self, mocked):
        with boddle(params={'owner': 'myowner', 'token': 'mytoken', 'repo': 'myrepo', 'branch': 'mybranch'}):
            data = {
                'object': {'sha': 'mysha'},
                'sha': 'mysha',
                'author': {
                    'name': 'myname',
                    'email': 'myemail'
                },
                'message': 'mymessage',
                'html_url': 'myurl'
            }

            mocked.return_value = MockResponse(200, json_result=[[data], data])

            self.assertEqual(get_commit(), {
                'sha': 'mysha',
                'branch': 'mybranch',
                'author': {
                    'name': 'myname',
                    'email': 'myemail'
                },
                'message': 'mymessage',
                'url': 'myurl'
            })

    @mock.patch('api.execute_api')
    def test_get_commit_for_sha_failed(self, mocked):
        with boddle(params={'owner': 'myowner', 'token': 'mytoken', 'repo': 'myrepo', 'sha': 'mysha'}):
            mocked.return_value = MockResponse(404)
            self.assertEqual(get_commit(), {'message': 'internal server error'})

        mocked.assert_called_once()

    @mock.patch('api.execute_api')
    def test_get_commit_for_sha(self, mocked):
        with boddle(params={'owner': 'myowner', 'token': 'mytoken', 'repo': 'myrepo', 'sha': 'mysha'}):
            mocked.return_value = MockResponse(200, json_result=[{
                'sha': 'mysha',
                'author': {
                    'name': 'myname',
                    'email': 'myemail'
                },
                'message': 'mymessage',
                'html_url': 'myurl'
            }])

            self.assertEqual(get_commit(), {
                'sha': 'mysha',
                'branch': None,
                'author': {
                    'name': 'myname',
                    'email': 'myemail'
                },
                'message': 'mymessage',
                'url': 'myurl'
            })

        mocked.assert_called_once()

if __name__ == '__main__':
    with open('results.xml', 'wb') as output:
        unittest.main(testRunner=xmlrunner.XMLTestRunner(output=output))
