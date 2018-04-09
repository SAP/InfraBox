import unittest

from pyinfrabox.testresult import validate_result
from pyinfrabox import ValidationError

class TestDockerCompose(unittest.TestCase):
    def raises_expect(self, data, expected):
        try:
            validate_result(data)
            assert False
        except ValidationError as e:
            self.assertEqual(e.message, expected)

    def test_version(self):
        self.raises_expect({}, "#: property 'version' is required")
        self.raises_expect({'version': 'asd', 'tests': []}, "#version: must be an int")
        self.raises_expect({'version': '1', 'tests': []}, "#version: must be an int")
        self.raises_expect({'version': 2, 'tests': []}, "#version: unsupported version")

    def test_ts(self):
        self.raises_expect({'version': 1}, "#: property 'tests' is required")
        self.raises_expect({'version': 1, 'tests': 'asd'}, "#tests: must be an array")
        self.raises_expect({'version': 1, 'tests': []}, "#tests: must not be empty")
