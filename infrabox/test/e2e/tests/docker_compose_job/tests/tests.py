import requests
import unittest

class Test(unittest.TestCase):
    def test_get(self):
        print("get")
        r = requests.get("http://test-server:3000")
        self.assertEqual(r.json(), {"hello": "world"})

if __name__ == '__main__':
    unittest.main()
