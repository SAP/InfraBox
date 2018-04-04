from builtins import int, range

from pyinfrabox import ValidationError
from pyinfrabox.utils import check_allowed_properties, check_required_properties, check_number, check_color, check_text

def check_version(v, path):
    if not isinstance(v, int):
        raise ValidationError(path, "must be an int")

    if v != 1:
        raise ValidationError(path, "unsupported version")

def parse_heading(d, path):
    check_allowed_properties(d, path, ("type", "text"))
    check_required_properties(d, path, ("type", "text"))
    check_text(d['text'], path + ".text")

def parse_hline(d, path):
    check_allowed_properties(d, path, ("type",))
    check_required_properties(d, path, ("type",))

def parse_text(d, path):
    check_allowed_properties(d, path, ("type", "text", "emphasis", "color"))
    check_required_properties(d, path, ("type", "text"))

    check_text(d['text'], path + ".text")

    if 'emphasis' in d:
        if d['emphasis'] not in ("bold", "italic"):
            raise ValidationError(path + ".emphasis", "not a valid value")

    if 'color' in d:
        check_color(d['color'], path + ".color")

def parse_icon(d, path):
    check_allowed_properties(d, path, ("type", "name", "color"))
    check_required_properties(d, path, ("type", "name"))
    check_text(d['name'], path + ".name")

    if 'color' in d:
        check_color(d['color'], path + ".color")

def parse_pie(d, path):
    check_allowed_properties(d, path, ("type", "data", "name"))
    check_required_properties(d, path, ("type", "data", "name"))
    check_text(d['name'], path + ".name")

    for i in range(0, len(d['data'])):
        elem = d['data'][i]
        p = "%s.data[%s]" % (path, i)

        check_allowed_properties(elem, p, ("label", "value", "color"))
        check_required_properties(elem, p, ("label", "value", "color"))

        check_text(elem['label'], p + ".label")
        check_number(elem['value'], p + ".value")
        check_color(elem['color'], p + ".color")

def parse_ordered_list(d, path):
    check_allowed_properties(d, path, ("type", "elements"))
    check_required_properties(d, path, ("type", "elements"))
    parse_elements(d['elements'], path + ".elements")

def parse_unordered_list(d, path):
    check_allowed_properties(d, path, ("type", "elements"))
    check_required_properties(d, path, ("type", "elements"))
    parse_elements(d['elements'], path + ".elements")

def parse_group(d, path):
    check_allowed_properties(d, path, ("type", "elements"))
    check_required_properties(d, path, ("type", "elements"))
    parse_elements(d['elements'], path + ".elements")

def parse_paragraph(d, path):
    check_allowed_properties(d, path, ("type", "elements"))
    check_required_properties(d, path, ("type", "elements"))
    parse_elements(d['elements'], path + ".elements")

def parse_grid(d, path):
    check_allowed_properties(d, path, ("type", "rows"))
    check_required_properties(d, path, ("type", "rows"))

    if not isinstance(d['rows'], list):
        raise ValidationError(path + ".rows", "must be an array")

    if not d['rows']:
        raise ValidationError(path + ".rows", "must not be empty")

    for i in range(0, len(d['rows'])):
        r = d['rows'][i]
        parse_elements(r, "%s.rows[%s]" % (path, i))

def parse_table(d, path):
    check_allowed_properties(d, path, ("type", "rows", "headers"))
    check_required_properties(d, path, ("type", "rows"))

    if 'headers' in d:
        if not isinstance(d['headers'], list):
            raise ValidationError(path + ".headers", "must be an array")

        col_count = len(d['headers'])
        if col_count == 0:
            raise ValidationError(path + ".headers", "must not be empty")

        for i in range(0, col_count):
            h = d['headers'][i]
            parse_text(h, "%s.headers[%s]" % (path, i))


    if not isinstance(d['rows'], list):
        raise ValidationError(path + ".rows", "must be an array")

    if not d['rows']:
        raise ValidationError(path + ".rows", "must not be empty")

    for i in range(0, len(d['rows'])):
        r = d['rows'][i]
        p = "%s.rows[%s]" % (path, i)

        if 'headers' in d:
            if len(r) != col_count:
                raise ValidationError(p, "does not have the correct number of columns")

        parse_elements(r, p)


def parse_elements(e, path):
    if not isinstance(e, list):
        raise ValidationError(path, "must be an array")

    if not e:
        raise ValidationError(path, "must not be empty")

    for i in range(0, len(e)):
        elem = e[i]
        p = "%s[%s]" % (path, i)

        if 'type' not in elem:
            raise ValidationError(p, "does not contain a 'type'")

        t = elem['type']

        if t == 'h1' or t == 'h2' or t == 'h3' or t == 'h4' or t == 'h5':
            parse_heading(elem, p)
        elif t == 'hline':
            parse_hline(elem, p)
        elif t == 'paragraph':
            parse_paragraph(elem, p)
        elif t == 'text':
            parse_text(elem, p)
        elif t == 'ordered_list':
            parse_ordered_list(elem, p)
        elif t == 'unordered_list':
            parse_unordered_list(elem, p)
        elif t == 'group':
            parse_group(elem, p)
        elif t == 'pie':
            parse_pie(elem, p)
        elif t == 'grid':
            parse_grid(elem, p)
        elif t == 'table':
            parse_table(elem, p)
        elif t == 'icon':
            parse_icon(elem, p)
        else:
            raise ValidationError(p, "type '%s' not supported" % t)

def parse_document(d):
    check_allowed_properties(d, "#", ("version", "title", "elements"))
    check_required_properties(d, "#", ("version", "title", "elements"))

    check_version(d['version'], "#version")
    check_text(d['title'], "#title")
    parse_elements(d['elements'], "#elements")

def validate_markup(d):
    parse_document(d)
