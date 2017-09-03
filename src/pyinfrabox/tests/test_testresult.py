from nose.tools import eq_, assert_raises

from pyinfrabox.testresult import *
from pyinfrabox import ValidationError

def raises_expect(data, expected):
    with assert_raises(ValidationError) as e:
        validate_result(data)

    eq_(e.exception.message, expected)

def test_version():
    raises_expect({}, "#: property 'version' is required")
    raises_expect({'version': 'asd', 'tests': []}, "#version: must be an int")
    raises_expect({'version': '1', 'tests': []}, "#version: must be an int")
    raises_expect({'version': 2, 'tests': []}, "#version: unsupported version")

def test_ts():
    raises_expect({'version': 1}, "#: property 'tests' is required")
    raises_expect({'version': 1, 'tests': 'asd'}, "#tests: must be an array")
    raises_expect({'version': 1, 'tests': []}, "#tests: must not be empty")
