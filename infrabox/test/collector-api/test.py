import unittest
import sys

from xmlrunner import XMLTestRunner

from collector_test import CollectorTest


if __name__ == '__main__':

    with open('results.xml', 'wb') as output:
        suite = unittest.TestSuite()
        #unittest.main(testRunner=xmlrunner.XMLTestRunner(output=output))
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(CollectorTest))

        testRunner = XMLTestRunner(output=output)
        #unittest.main(testRunner = XMLTestRunner(output=output),
        #              failfast=False, buffer=False, catchbreak=False)
        ret = testRunner.run(suite).wasSuccessful()
        sys.exit(not ret)
