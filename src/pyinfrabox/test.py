import unittest
import xmlrunner

if __name__ == '__main__':
    with open('results.xml', 'wb') as output:
        s = unittest.defaultTestLoader.discover('.')
        testRunner=xmlrunner.XMLTestRunner(output=output).run(s)
