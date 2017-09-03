from builtins import int, range

from pyinfrabox import ValidationError
from pyinfrabox.utils import *

def check_version(v, path):
    if not isinstance(v, int):
        raise ValidationError(path, "must be an int")

    if v != 1:
        raise ValidationError(path, "unsupported version")

def parse_measurement(d, path):
    check_allowed_properties(d, path, ("name", "unit", "value"))
    check_required_properties(d, path, ("name", "unit", "value"))
    check_text(d['unit'], path + ".unit")
    check_text(d['name'], path + ".name")
    check_text(d['value'], path + ".value")

def parse_measurements(e, path):
    if not isinstance(e, list):
        raise ValidationError(path, "must be an array")

    for i in range(0, len(e)):
        elem = e[i]
        path = "%s[%s]" % (path, i)
        parse_measurement(elem, path)

def parse_t(d, path):
    check_allowed_properties(d, path,
                             ("suite", "name", "status", "duration", "message",
                              "stack", "measurements"))
    check_required_properties(d, path, ("suite", "name", "status", "duration"))
    check_text(d['suite'], path + ".suite")
    check_text(d['name'], path + ".name")
    check_text(d['status'], path + ".status")
    check_number(d['duration'], path + ".duration")

    if 'message' in d:
        check_text(d['message'], path + ".message")

    if 'stack' in d:
        check_text(d['stack'], path + ".stack")

    if 'measurements' in d:
        parse_measurements(d['measurements'], path + ".measurements")

def parse_ts(e, path):
    if not isinstance(e, list):
        raise ValidationError(path, "must be an array")

    if not e:
        raise ValidationError(path, "must not be empty")

    for i in range(0, len(e)):
        elem = e[i]
        path = "%s[%s]" % (path, i)
        parse_t(elem, path)

def parse_document(d):
    check_allowed_properties(d, "#", ("version", "tests"))
    check_required_properties(d, "#", ("version", "tests"))

    check_version(d['version'], "#version")
    parse_ts(d['tests'], "#tests")

def validate_result(d):
    parse_document(d)
