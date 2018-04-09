from pyinfrabox import ValidationError
from pyinfrabox.utils import *
from builtins import int

def check_version(v, path):
    if not isinstance(v, int):
        raise ValidationError(path, "must be an int")

    if v != 1:
        raise ValidationError(path, "unsupported version")


def parse_badge(d):
    check_allowed_properties(d, "#", ("version", "subject", "status", "color"))
    check_required_properties(d, "#", ("version", "subject", "status", "color"))
    check_version(d['version'], "#version")

    check_text(d['subject'], "#subject")
    check_text(d['status'], "#status")
    check_color(d['color'], "#color")

def validate_badge(d):
    parse_badge(d)
