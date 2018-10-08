import os
import unittest

from pyinfrabox.docker_compose import create_from

class TestDockerCompose(unittest.TestCase):
    def run_exception(self, path, message):
        path = os.path.join(os.path.dirname(os.path.realpath(__file__)), path)

        try:
            create_from(path)
            assert False
        except Exception as e:
            print(e)
            self.assertEqual(e.message, message)

    def test_empty(self):
        self.run_exception('./test/empty.yml', 'invalid file')

    def test_no_version(self):
        self.run_exception('./test/no_version.yml', 'version not found')

    def test_unsupported_version(self):
        self.run_exception('./test/unsupported_version.yml', 'version not supported, supported version is 3.2')

    def test_invalid_version(self):
        self.run_exception('./test/invalid_version.yml', 'version not supported, supported version is 3.2')

    def test_unsupported_option(self):
        self.run_exception('./test/unsupported_option.yml', '[services][test][expose] not supported')

    def test_no_services(self):
        self.run_exception('./test/no_services.yml', 'services not found')

    def test_unsupported_top_level(self):
        self.run_exception('./test/unsupported_top_level.yml', '[blub] not supported')

    def test_valid_1(self):
        create_from('./tests/test/valid_1.yml')
