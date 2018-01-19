from xml.etree import ElementTree

RESULT_MAPPING = {
    'failure': 'fail',
    'error': 'error',
    'skipped': 'skipped'
}

def get_ms(val):
    return int(float(val) * 1000)

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
        ts_name = root.attrib.get('name')

        for el in root:
            if el.tag != 'testcase':
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
        classname = el.attrib.get('classname')

        if classname:
            suite += ' = ' + classname

        tc = {
            "measurements":  [],
            "name": el.attrib['name'],
            "status":  'ok',
            "suite": suite,
            "duration": duration
        }

        message = el.attrib.get('message', '')
        if message is None:
            message = error

        if message is None:
            message = ''

        stack = ''
        if error:
            stack += error

        for e in el:
            if e.tag in ('failure', 'error', 'skipped'):
                if e.text:
                    stack += '\n'
                    stack += e.text

                tc['status'] = RESULT_MAPPING[e.tag]
                tc['message'] = message
                tc['stack'] = stack

        return tc
