class MockResponse(object):
    def __init__(self, status_code, json_result=None):
        self.status_code = status_code
        self.json_result = json_result

    def json(self):
        return self.json_result
