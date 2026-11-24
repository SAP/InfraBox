import io
import base64
import json
import logging
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import Mock, patch

from infrabox_job.job import Job
from infrabox_job.process import ApiConsole
from infrabox_job.secret_masker import MASKING_FAILED, SecretMasker, SecretMaskingFormatter


class SecretMaskerTest(unittest.TestCase):
    def test_registration_failure_suppresses_later_output(self):
        masker = SecretMasker()
        with patch.object(masker, '_add', side_effect=RuntimeError('dummy-registration-secret')):
            masker.add('dummy-registration-secret')
        self.assertEqual(masker.mask('dummy-registration-secret\n'), MASKING_FAILED + '\n')
        self.assertEqual(masker.mask('ordinary output'), MASKING_FAILED)

    def test_sensitive_field_registration_failure_suppresses_output(self):
        masker = SecretMasker()
        with patch('infrabox_job.secret_masker.re.search', side_effect=RuntimeError('dummy-secret')):
            masker.add_sensitive_fields({'PASSWORD': 'dummy-secret'})
        self.assertEqual(masker.mask('dummy-secret'), MASKING_FAILED)

    def test_formatter_failure_does_not_expose_raw_record_through_logging_error(self):
        output = io.StringIO()
        errors = io.StringIO()
        masker = SecretMasker()
        formatter = Mock()
        formatter.format.side_effect = RuntimeError('dummy-formatting-secret')
        handler = logging.StreamHandler(output)
        handler.setFormatter(SecretMaskingFormatter(masker, formatter))
        logger = logging.Logger('formatting-fault-test')
        logger.addHandler(handler)
        with redirect_stderr(errors):
            logger.error('credential=%s', 'dummy-formatting-secret')
        self.assertEqual(output.getvalue(), MASKING_FAILED + '\n')
        self.assertEqual(errors.getvalue(), '')
        self.assertEqual(masker.mask('later secret output'), MASKING_FAILED)

    def test_empty_values_literal_matching_and_longest_match(self):
        masker = SecretMasker()
        for value in (None, '', ' \n', 'fake-token', 'fake-token-long', 'a.*[b]'):
            masker.add(value)
        self.assertEqual(masker.mask('fake-token-long fake-token a.*[b] ordinary output'),
                         '**** **** **** ordinary output')
        masker.add('later-value')
        self.assertEqual(masker.mask('later-value'), '****')

    def test_multiline_json_credentials_and_reformatted_values(self):
        private_key = '-----BEGIN PRIVATE KEY-----\nFAKE-KEY-LINE-ONE\nFAKE-KEY-LINE-TWO\n-----END PRIVATE KEY-----\n'
        credential = {'private_key': private_key, 'client_secret': 'dummy-"quoted"-密钥'}
        masker = SecretMasker()
        masker.add(json.dumps(credential, indent=2))
        for output in (json.dumps(credential), json.dumps(credential, indent=4, ensure_ascii=False), private_key):
            with self.subTest(output=output):
                masked = ''.join(masker.mask(line) for line in output.splitlines(keepends=True))
                self.assertNotIn('FAKE-KEY-LINE', masked)
                self.assertNotIn('dummy-', masked)
        self.assertEqual(masker.mask('ordinary {braces} remain'), 'ordinary {braces} remain')

    def test_logging_formatter_masks_arguments_and_traceback(self):
        masker = SecretMasker()
        masker.add('dummy-exception-secret')
        output = io.StringIO()
        handler = logging.StreamHandler(output)
        handler.setFormatter(SecretMaskingFormatter(masker, logging.Formatter('%(levelname)s %(message)s')))
        logger = logging.Logger('secret-masking-test')
        logger.addHandler(handler)
        try:
            raise ValueError('dummy-exception-secret')
        except ValueError:
            logger.exception('Failed with %s', 'dummy-exception-secret')
        self.assertIn('ERROR Failed with ****', output.getvalue())
        self.assertIn('ValueError: ****', output.getvalue())
        self.assertNotIn('dummy-exception-secret', output.getvalue())


class ConsoleMaskingTest(unittest.TestCase):
    def setUp(self):
        self.console = ApiConsole()
        self.console.masker.add('dummy-password')
        self.output = io.StringIO()

    def test_masking_failure_drains_large_subprocess_output_and_preserves_success(self):
        with tempfile.TemporaryDirectory() as directory:
            completed = Path(directory) / 'completed'
            script = (
                'import pathlib, sys; '
                'sys.stdout.write(("dummy-password" * 100 + "\\n") * 2000); '
                'sys.stderr.write("dummy-password\\n"); '
                'pathlib.Path(sys.argv[1]).write_text("completed")'
            )
            with patch('infrabox_job.secret_masker.re.compile', side_effect=RuntimeError('dummy-password')):
                with redirect_stdout(self.output):
                    self.console.execute([sys.executable, '-c', script, str(completed)], show_cmd=False)
            self.assertEqual(completed.read_text(), 'completed')
        self.assertNotIn('dummy-password', self.output.getvalue())
        self.assertEqual(self.output.getvalue().count(MASKING_FAILED), 2001)
        self.assertEqual(self.console.masker.mask('later output'), MASKING_FAILED)

    def test_masking_failure_preserves_failed_command_status(self):
        command = [sys.executable, '-c', 'import sys; print("dummy-password"); sys.exit(7)']
        with patch('infrabox_job.secret_masker.re.compile', side_effect=RuntimeError('dummy-password')):
            with redirect_stdout(self.output):
                with self.assertRaises(Exception) as raised:
                    self.console.execute(command, show_cmd=False)
        self.assertEqual(str(raised.exception), 'Command failed')
        self.assertEqual(self.output.getvalue(), MASKING_FAILED + '\n')

    def test_commands_stdout_stderr_and_environment_are_masked(self):
        script = (
            'import os, sys; '
            'value = os.environ["PASSWORD"]; '
            'assert value == "dummy-password"; '
            'print("PASSWORD=" + value, flush=True); '
            'print("stderr=" + value, file=sys.stderr, flush=True); '
            'print("ordinary output", flush=True)'
        )
        with redirect_stdout(self.output):
            self.console.execute([sys.executable, '-c', script], show=True,
                                 env={'PASSWORD': 'dummy-password'})
        output = self.output.getvalue()
        self.assertNotIn('dummy-password', output)
        self.assertIn('PASSWORD=****\nstderr=****\nordinary output\n', output)

    def test_hidden_command_still_masks_output_split_between_writes_and_eof(self):
        script = (
            'import os; '
            'os.write(1, b"dummy-"); '
            'os.write(1, b"password\\n"); '
            'os.write(2, b"dummy-password")'
        )
        with redirect_stdout(self.output):
            self.console.execute([sys.executable, '-c', script], show=False)
        self.assertEqual(self.output.getvalue(), '****\n****')

    def test_execute_mask_registers_value_even_when_command_is_hidden(self):
        with redirect_stdout(self.output):
            self.console.execute_mask([sys.executable, '-c', 'print("dummy-git-token")'],
                                      show_cmd=False, mask='dummy-git-token')
        self.assertEqual(self.output.getvalue(), '****\n')

    def test_failed_commands_mask_output_and_preserve_ignore_error(self):
        command = [sys.executable, '-c', 'import sys; print("dummy-password"); sys.exit(7)']
        with redirect_stdout(self.output):
            with self.assertRaisesRegex(Exception, 'Command failed'):
                self.console.execute(command)
            self.console.execute(command, ignore_error=True)
        self.assertEqual(self.output.getvalue(), '****\n****\n')

    @patch('infrabox_job.process.time.sleep')
    def test_retries_remain_masked(self, sleep):
        command = [sys.executable, '-c', 'import sys; print("dummy-password"); sys.exit(7)']
        with redirect_stdout(self.output):
            with self.assertRaisesRegex(Exception, 'Command failed'):
                self.console.execute(command, retry=True)
        self.assertEqual(self.output.getvalue(), '****\n' * 5)
        self.assertEqual(sleep.call_count, 5)


class JobSecretRegistrationTest(unittest.TestCase):
    @patch.dict(os.environ, {'INFRABOX_GENERAL_SYSTEM_NAMESPACE': 'infrabox-system',
                            'INFRABOX_JOB_TOKEN': 'dummy-bootstrap-token'})
    @patch('infrabox_job.job.time.sleep')
    def test_bootstrap_exception_is_masked_before_job_data_is_loaded(self, _sleep):
        output = io.StringIO()
        with patch('infrabox_job.job.requests.get',
                   side_effect=[RuntimeError('dummy-bootstrap-token'), Mock(status_code=409)]):
            with redirect_stdout(output), self.assertRaises(SystemExit):
                Job().load_data()
        self.assertIn('RuntimeError: ****', output.getvalue())
        self.assertNotIn('dummy-bootstrap-token', output.getvalue())

    @patch.dict(os.environ, {'INFRABOX_GENERAL_SYSTEM_NAMESPACE': 'infrabox-system'})
    def test_resource_token_is_masked_in_encoded_and_decoded_forms(self):
        token = 'dummy-kubernetes-token'
        encoded = base64.b64encode(token.encode('utf-8')).decode('ascii')
        with patch.dict(os.environ, {'INFRABOX_RESOURCES_KUBERNETES_TOKEN': encoded}):
            job = Job()
        self.assertEqual(job.console.masker.mask(token + ' ' + encoded), '**** ****')

    @patch.dict(os.environ, {'INFRABOX_GENERAL_SYSTEM_NAMESPACE': 'infrabox-system',
                            'INFRABOX_JOB_TOKEN': 'dummy-job-token'})
    @patch('infrabox_job.job.time.sleep')
    def test_loading_registers_job_credentials_without_changing_injected_values(self, _sleep):
        response = Mock(status_code=200)
        credential = json.dumps({'private_key': 'dummy-private-key'})
        response.json.return_value = {
            'job': {}, 'project': {}, 'build': {}, 'commit': {}, 'dependencies': [], 'parents': [],
            'repository': {'github_api_token': 'dummy-github-token'},
            'env_vars': {'PUBLIC': 'ordinary-value', 'DEFAULT_ADMIN_PASSWORD': 'dummy-admin-password'},
            'secrets': {'PASSWORD': 'dummy-project-secret', 'VAULT_CREDENTIAL': credential},
            'registries': [{'password': 'dummy-registry-password', 'host': 'registry.example'}],
            'deployments': [{'secret_access_key': 'dummy-deployment-key'}],
        }
        output = io.StringIO()
        job = Job()
        with patch('infrabox_job.job.requests.get', return_value=response), redirect_stdout(output):
            job.load_data()
            for name, value in job.environment.items():
                job.console.collect('%s=%s' % (name, value), show=True)
            job.console.collect('dummy-job-token dummy-github-token dummy-registry-password dummy-deployment-key',
                                show=True)
        self.assertEqual(job.environment['PASSWORD'], 'dummy-project-secret')
        self.assertEqual(job.environment['VAULT_CREDENTIAL'], credential)
        self.assertEqual(job.environment['DEFAULT_ADMIN_PASSWORD'], 'dummy-admin-password')
        self.assertNotIn('dummy-', output.getvalue())
        self.assertIn('PUBLIC=ordinary-value', output.getvalue())


if __name__ == '__main__':
    unittest.main()
