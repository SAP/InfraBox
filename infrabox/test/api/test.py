import unittest

from xmlrunner import XMLTestRunner

from job_api_test import JobApiTest
from build_test import BuildTest
from job_test import JobTest
from project_test import ProjectTest
from trigger_test import TriggerTest
from tokens_test import TokensTest
from secrets_test import SekretsTest
from collaborators_test import CollaboratorsTest

from pyinfraboxutils.storage import storage


if __name__ == '__main__':
    storage.create_buckets()

    with open('results.xml', 'wb') as output:
        suite = unittest.TestSuite()
        #unittest.main(testRunner=xmlrunner.XMLTestRunner(output=output))
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(ProjectTest))
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TriggerTest))
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(JobApiTest))
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(BuildTest))
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(JobTest))
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(CollaboratorsTest))
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TokensTest))
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(SekretsTest))

        testRunner = XMLTestRunner(output=output)
        #unittest.main(testRunner = XMLTestRunner(output=output),
        #              failfast=False, buffer=False, catchbreak=False)
        testRunner.run(suite)
