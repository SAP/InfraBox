import unittest
import xmlrunner

if __name__ == '__main__':
    s = unittest.defaultTestLoader.discover('.')
    xmlrunner.XMLTestRunner(output='/infrabox/output/upload/testresult').run(s)
