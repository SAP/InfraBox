import unittest
import sys
import xmlrunner

if __name__ == '__main__':
    s = unittest.defaultTestLoader.discover('.')
    r = xmlrunner.XMLTestRunner(output='/infrabox/upload/testresult/').run(s)
    sys.exit(not r.wasSuccessful())
