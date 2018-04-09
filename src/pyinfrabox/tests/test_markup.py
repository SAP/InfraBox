import json
import os
import unittest

from pyinfrabox.markup import parse_document, parse_text, parse_ordered_list
from pyinfrabox.markup import parse_unordered_list, parse_group, parse_paragraph
from pyinfrabox.markup import parse_grid, parse_table
from pyinfrabox import ValidationError

class TestDockerCompose(unittest.TestCase):
    def raises_expect(self, data, expected):
        try:
            parse_document(data)
            assert False
        except ValidationError as e:
            self.assertEqual(e.message, expected)


    def test_version(self):
        self.raises_expect({}, "#: property 'version' is required")
        self.raises_expect({'version': 'asd', 'elements': [], 'title': "t"}, "#version: must be an int")
        self.raises_expect({'version': '1', 'elements': [], 'title': "t"}, "#version: must be an int")
        self.raises_expect({'version': 2, 'elements': [], 'title': "t"}, "#version: unsupported version")

    def test_title(self):
        self.raises_expect({'version': 1}, "#: property 'title' is required")
        self.raises_expect({'version': 1, 'elements': [], 'title': 123}, "#title: is not a string")
        self.raises_expect({'version': 1, 'elements': [], 'title': ""}, "#title: empty string not allowed")

    def test_elements(self):
        self.raises_expect({'version': 1, 'title': 'title'}, "#: property 'elements' is required")
        self.raises_expect({'version': 1, 'title': 'title', 'elements': 'asd'}, "#elements: must be an array")
        self.raises_expect({'version': 1, 'title': 'title', 'elements': []}, "#elements: must not be empty")
        self.raises_expect({'version': 1, 'title': 'title', 'elements': [{}]},
                           "#elements[0]: does not contain a 'type'")

    def test_heading(self):
        for h in ("h1", "h2", "h3", "h4", "h5"):
            d = {'version': 1, 'title': 'title', 'elements': []}

            d['elements'] = [{'type': h}]
            self.raises_expect(d, "#elements[0]: property 'text' is required")

            d['elements'] = [{'type': h, "text": ""}]
            self.raises_expect(d, "#elements[0].text: empty string not allowed")

            d['elements'] = [{'type': h, "text": 1}]
            self.raises_expect(d, "#elements[0].text: is not a string")

    def test_unsupported_type(self):
        d = {'version': 1, 'title': 'title', 'elements': []}
        d['elements'] = [{'type': 'somethingweird'}]
        self.raises_expect(d, "#elements[0]: type 'somethingweird' not supported")

    def test_hline(self):
        d = {'version': 1, 'title': 'title', 'elements': []}

        d['elements'] = [{'type': 'hline', "addition": True}]
        self.raises_expect(d, "#elements[0]: invalid property 'addition'")


    def test_text(self):
        def raises_expect_text(data, expected):
            try:
                parse_text(data, "#")
                assert False
            except ValidationError as e:
                self.assertEqual(e.message, expected)

        raises_expect_text({}, "#: property 'type' is required")
        raises_expect_text({"type": "text"}, "#: property 'text' is required")
        raises_expect_text({"type": "text", "text": 123}, "#.text: is not a string")
        raises_expect_text({"type": "text", "text": ""}, "#.text: empty string not allowed")
        raises_expect_text({"type": "text", "text": "t", "color": "dunno"}, "#.color: not a valid value")
        raises_expect_text({"type": "text", "text": "t", "emphasis": "dunno"}, "#.emphasis: not a valid value")

        parse_text({"type": "text", "text": "t", "color": "red", "emphasis": "bold"}, "")

        d = {'version': 1, 'title': 'title', 'elements': [{"type": "text", "text": "t",
                                                           "color": "red", "emphasis": "bold"}]}
        parse_document(d)

    def test_ordered_list(self):
        def raises_expect_list(data, expected):
            try:
                parse_ordered_list(data, "#")
                assert False
            except ValidationError as e:
                self.assertEqual(e.message, expected)

        raises_expect_list({}, "#: property 'type' is required")
        raises_expect_list({"type": "ordered_list"}, "#: property 'elements' is required")
        raises_expect_list({"type": "ordered_list", "elements": 123}, "#.elements: must be an array")
        raises_expect_list({"type": "ordered_list", "elements": []}, "#.elements: must not be empty")

        parse_ordered_list({"type": "ordered_list", "elements": [{"type": "hline"}]}, "")

        d = {'version': 1, 'title': 'title', 'elements': [{"type": "ordered_list", "elements": [{"type": "hline"}]}]}
        parse_document(d)

    def test_unordered_list(self):
        def raises_expect_list(data, expected):
            try:
                parse_unordered_list(data, "#")
                assert False
            except ValidationError as e:
                self.assertEqual(e.message, expected)

        raises_expect_list({}, "#: property 'type' is required")
        raises_expect_list({"type": "unordered_list"}, "#: property 'elements' is required")
        raises_expect_list({"type": "unordered_list", "elements": 123}, "#.elements: must be an array")
        raises_expect_list({"type": "unordered_list", "elements": []}, "#.elements: must not be empty")

        parse_ordered_list({"type": "unordered_list", "elements": [{"type": "hline"}]}, "")

        d = {'version': 1, 'title': 'title', 'elements': [{"type": "unordered_list", "elements": [{"type": "hline"}]}]}
        parse_document(d)

    def test_group(self):
        def raises_expect_group(data, expected):
            try:
                parse_unordered_list(data, "#")
                assert False
            except ValidationError as e:
                self.assertEqual(e.message, expected)

        raises_expect_group({}, "#: property 'type' is required")
        raises_expect_group({"type": "group"}, "#: property 'elements' is required")
        raises_expect_group({"type": "group", "elements": 123}, "#.elements: must be an array")
        raises_expect_group({"type": "group", "elements": []}, "#.elements: must not be empty")

        parse_group({"type": "group", "elements": [{"type": "hline"}]}, "")

        d = {'version': 1, 'title': 'title', 'elements': [{"type": "group", "elements": [{"type": "hline"}]}]}
        parse_document(d)

    def test_paragraph(self):
        def raises_expect_p(data, expected):
            try:
                parse_unordered_list(data, "#")
                assert False
            except ValidationError as e:
                self.assertEqual(e.message, expected)

        raises_expect_p({}, "#: property 'type' is required")
        raises_expect_p({"type": "paragraph"}, "#: property 'elements' is required")
        raises_expect_p({"type": "paragraph", "elements": 123}, "#.elements: must be an array")
        raises_expect_p({"type": "paragraph", "elements": []}, "#.elements: must not be empty")

        parse_paragraph({"type": "paragraph", "elements": [{"type": "hline"}]}, "")

        d = {'version': 1, 'title': 'title', 'elements': [{"type": "paragraph", "elements": [{"type": "hline"}]}]}
        parse_document(d)

    def test_grid(self):
        def raises_expect_grid(data, expected):
            try:
                parse_grid(data, "#")
                assert False
            except ValidationError as e:
                self.assertEqual(e.message, expected)

        raises_expect_grid({}, "#: property 'type' is required")
        raises_expect_grid({"type": "grid"}, "#: property 'rows' is required")
        raises_expect_grid({"type": "grid", "rows": 123}, "#.rows: must be an array")
        raises_expect_grid({"type": "grid", "rows": []}, "#.rows: must not be empty")
        raises_expect_grid({"type": "grid", "rows": [{"type": "hline"}]}, "#.rows[0]: must be an array")

        parse_grid({"type": "grid", "rows": [[{"type": "hline"}]]}, "")

        d = {'version': 1, 'title': 'title',
             'elements': [{"type": "grid", "rows": [[{"type": "hline"}], [{"type": "hline"}]]}]}
        parse_document(d)

    def test_table(self):
        def raises_expect_table(data, expected):
            try:
                parse_table(data, "#")
                assert False
            except ValidationError as e:
                self.assertEqual(e.message, expected)

        raises_expect_table({}, "#: property 'type' is required")
        raises_expect_table({"type": "table"}, "#: property 'rows' is required")
        raises_expect_table({"type": "table", "rows": 123, "headers": [{"type": "text", "text": "t"}]},
                            "#.rows: must be an array")

        raises_expect_table({"type": "table", "rows": [], "headers": [{"type": "text", "text": "t"}]},
                            "#.rows: must not be empty")
        raises_expect_table({"type": "table", "rows": [{"type": "hline"}], "headers": [{"type": "text", "text": "t"}]},
                            "#.rows[0]: must be an array")
        raises_expect_table({"type": "table", "rows": [[{"type": "hline"}]],
                             "headers": [[{"type": "text", "text": " "}]]},
                            "#.headers[0]: must be an object")

        parse_table({"type": "table", "rows": [[{"type": "hline"}]], "headers": [{"type": "text", "text": " "}]}, "")

        d = {'version': 1, 'title': 'title', 'elements': [
            {"type": "table", "rows": [[{"type": "hline"}]], "headers": [{"type": "text", "text": " "}]}
        ]}
        parse_document(d)

    def test_valid(self):
        p = os.path.dirname(os.path.realpath(__file__))
        fp = os.path.join(p, "./test/valid_markup.json")
        with open(fp) as f:
            d = json.load(f)
            parse_document(d)
