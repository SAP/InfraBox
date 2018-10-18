import unittest
from temp_tools import TestClient


class CollectorTest(unittest.TestCase):

    def setUp(self):
        pass

    def test_collector_ping(self):
        r = TestClient.get(url = 'ping', headers = None)
        self.assertEqual(r['status'], 200)

    def test_collector_pods(self):
        r = TestClient.get(url = 'api/pods', headers = None)
        self.assertEqual(r, [])
        

