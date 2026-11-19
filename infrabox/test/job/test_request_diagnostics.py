import io
import os
import unittest
import uuid
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

import requests
from flask import Flask, g

from infrabox_job.job import Job
from infrabox_job.process import Error
from pyinfraboxutils import request_diagnostics as diagnostics


class JobRequestTest(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {
            'INFRABOX_GENERAL_SYSTEM_NAMESPACE': 'infrabox-system',
            'INFRABOX_JOB_TOKEN': 'private-job-token',
            'INFRABOX_JOB_ID': 'test-job',
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.job = Job()

    @patch('infrabox_job.job.time.sleep')
    def test_timeout_is_flushed_before_retry_and_success_still_loads_secrets(self, _sleep):
        output = io.StringIO()
        flushed_output = []
        output.flush = Mock(side_effect=lambda: flushed_output.append(output.getvalue()))
        response = Mock(status_code=200)
        response.json.return_value = {
            'job': {'id': 'test-job'}, 'project': {}, 'build': {},
            'repository': {}, 'commit': {}, 'dependencies': [], 'parents': [],
            'env_vars': {'PUBLIC': 'value'}, 'secrets': {'PASSWORD': 'private-value'},
            'registries': [], 'deployments': [],
        }
        attempts = []
        output_before_attempt = []
        original_get_headers = self.job.get_headers

        def get_headers():
            output_before_attempt.append(flushed_output[-1] if flushed_output else '')
            return original_get_headers()

        def get(_url, **kwargs):
            attempts.append(kwargs['headers'].copy())
            if len(attempts) == 1:
                raise requests.exceptions.ReadTimeout('read timeout=10')
            if len(attempts) > 2:
                return Mock(status_code=409)
            return response

        with patch.object(self.job, 'get_headers', side_effect=get_headers), \
                patch('infrabox_job.job.requests.get', side_effect=get) as request_get, \
                redirect_stdout(output):
            self.job.load_data()

        self.assertEqual(request_get.call_count, 2)
        self.assertEqual(len(output_before_attempt), 2)
        self.assertIn('ReadTimeout', output_before_attempt[1])
        self.assertIn('Traceback (most recent call last)', output_before_attempt[1])
        for headers in attempts:
            uuid.UUID(headers['X-Request-ID'])
            self.assertEqual(headers['Authorization'], 'token private-job-token')
        self.assertNotEqual(attempts[0]['X-Request-ID'], attempts[1]['X-Request-ID'])
        self.assertIn('/api/job/job', output.getvalue())
        self.assertIn('attempt=2', output.getvalue())
        self.assertNotIn('private-job-token', output.getvalue())
        self.assertNotIn('private-value', output.getvalue())
        self.assertEqual(self.job.environment['PASSWORD'], 'private-value')

    @patch('infrabox_job.job.time.sleep')
    def test_api_error_message_is_preserved(self, _sleep):
        response = Mock(status_code=400)
        response.json.return_value = {'message': 'Vault authentication failed'}
        with patch('infrabox_job.job.requests.get', return_value=response), redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(Error, 'Vault authentication failed'):
                self.job.load_data()

    @patch('infrabox_job.job.time.sleep')
    def test_finished_job_still_exits_without_retry(self, _sleep):
        with patch('infrabox_job.job.requests.get', return_value=Mock(status_code=409)) as get:
            with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as raised:
                self.job.load_data()
        self.assertEqual(raised.exception.code, 0)
        get.assert_called_once()


class ServerDiagnosticsTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.request_id = str(uuid.uuid4())

    def test_stage_is_logged_before_blocking_operation_and_error_propagates(self):
        with self.app.test_request_context('/api/job/job', headers={'X-Request-ID': self.request_id}):
            with self.assertLogs(diagnostics.logger, level='WARNING') as logs:
                diagnostics.start_job_request()
                g.token = {'job': {'id': 'test-job'}}

                def database_query():
                    self.assertIn('stage=dependencies_query', logs.output[-1])
                    self.assertIn('stage started', logs.output[-1])
                    raise RuntimeError('query cancelled')

                with self.assertRaisesRegex(RuntimeError, 'query cancelled'):
                    diagnostics.trace_call('dependencies_query', database_query)

            text = os.linesep.join(logs.output)
            self.assertIn(self.request_id, text)
            self.assertIn('job_id=test-job', text)
            self.assertIn('stage failed', text)
            self.assertIn('Traceback', text)

    def test_response_has_matching_request_id_without_logging_secrets(self):
        with self.app.test_request_context('/api/job/job', headers={
            'X-Request-ID': self.request_id, 'Authorization': 'token private-token',
        }):
            with self.assertLogs(diagnostics.logger, level='WARNING') as logs:
                diagnostics.start_job_request()
                self.assertEqual(diagnostics.trace_call('vault_secret_read', lambda: 'private-value'), 'private-value')
                response = diagnostics.finish_job_request(self.app.response_class('private-payload', status=400))
            self.assertEqual(response.headers['X-Request-ID'], self.request_id)
            text = os.linesep.join(logs.output)
            self.assertIn('status=400', text)
            self.assertNotIn('private-token', text)
            self.assertNotIn('private-value', text)
            self.assertNotIn('private-payload', text)

    def test_untrusted_request_id_is_replaced(self):
        with self.app.test_request_context('/api/job/job', headers={'X-Request-ID': 'untrusted-text'}):
            with self.assertLogs(diagnostics.logger, level='WARNING') as logs:
                diagnostics.start_job_request()
            uuid.UUID(g.job_request_diagnostics['request_id'])
            self.assertNotIn('untrusted-text', os.linesep.join(logs.output))

    def test_other_endpoints_are_not_traced(self):
        with self.app.test_request_context('/api/v1/projects'):
            with patch.object(diagnostics.logger, 'warning') as warning:
                diagnostics.start_job_request()
                self.assertEqual(diagnostics.trace_call('database_pool', lambda: 42), 42)
                response = diagnostics.finish_job_request(self.app.response_class('ok'))
            warning.assert_not_called()
            self.assertNotIn('X-Request-ID', response.headers)

    def test_vault_calls_outside_http_requests_are_unchanged(self):
        @diagnostics.trace_stage('vault_secret_read')
        def vault_read():
            return 'value'

        self.assertEqual(vault_read(), 'value')


if __name__ == '__main__':
    unittest.main()
