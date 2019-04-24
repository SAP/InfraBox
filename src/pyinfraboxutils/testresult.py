from xml.etree import ElementTree
import uuid

RESULT_MAPPING = {
    'failure': 'fail',
    'error': 'error',
    'skipped': 'skipped'
}

def get_ms(val):
    try:
        return int(float(val) * 1000)
    except:
        return 0

class Parser(object):
    def __init__(self, i):
        self.input = i
        self.tests = []

    def parse(self, _badge_dir):
        xml = ElementTree.parse(self.input)
        root = xml.getroot()
        return self.parse_root(root)

    def parse_root(self, root):
        if root.tag == 'testsuites':
            for subroot in root:
                self.parse_testsuite(subroot)
        else:
            self.parse_testsuite(root)

        res = {
            "version": 1,
            "tests": self.tests
        }
        return res

    def parse_testsuite(self, root):
        assert root.tag == 'testsuite'
        ts_name = root.attrib.get('name', 'None')

        if not ts_name:
            ts_name = 'None'

        for el in root:
            if el.tag == 'testsuite':
                self.parse_testsuite(el)
                continue
            elif el.tag != 'testcase':
                continue

            error = root.find('error')

            if error is not None:
                error = error.text

            tc = self.parse_testcase(el, ts_name, error=error)
            self.tests.append(tc)

    def parse_testcase(self, el, ts_name, error=None):
        time = el.attrib.get('time')
        duration = 0
        if time:
            duration = get_ms(time)

        suite = ts_name

        tc = {
            "measurements":  [],
            "name": el.attrib.get('name', str(uuid.uuid4())),
            "status":  'ok',
            "suite": suite,
            "duration": duration
        }

        message = el.attrib.get('message', '')
        if message is None:
            message = error

        stack = None
        if error:
            stack = error

        for e in el:
            if e.tag in ('failure', 'error', 'skipped'):
                if e.text:
                    if not stack:
                        stack = ''

                    stack += '\n'
                    stack += e.text

                tc['status'] = RESULT_MAPPING[e.tag]

                if message:
                    tc['message'] = message

                if stack:
                    tc['stack'] = stack

        return tc
