import os

from nose.tools import eq_, assert_raises
from pyinfrabox.docker_compose import create_from

def run_exception(path, message):
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), path)

    with assert_raises(Exception) as e:
        create_from(path)

    eq_(e.exception.message, message)

def test_empty():
    run_exception('./test/empty.yml', 'invalid file')

def test_no_version():
    run_exception('./test/no_version.yml', 'version not found')

def test_unsupported_version():
    run_exception('./test/unsupported_version.yml', 'version \'3\' not supported, supported versions are: (\'3.2\',)')

def test_invalid_version():
    run_exception('./test/invalid_version.yml', 'version \'asd\' not supported, supported versions are: (\'3.2\',)')

def test_unsupported_option():
    run_exception('./test/unsupported_option.yml', '[services][test][expose] not supported')

def test_no_services():
    run_exception('./test/no_services.yml', 'services not found')

def test_unsupported_top_level():
    run_exception('./test/unsupported_top_level.yml', '[blub] not supported')

def test_valid_1():
    create_from('./tests/test/valid_1.yml')
