import unittest
import sys

from xmlrunner import XMLTestRunner

from job_api_test import JobApiTest
from build_test import BuildTest
from job_test import JobTest
from project_test import ProjectTest
from trigger_test import TriggerTest
from tokens_test import TokensTest
from secrets_test import SecretsTest
from collaborators_test import CollaboratorsTest
from user_test import UserTest

from pyinfraboxutils.storage import storage


if __name__ == '__main__':
    storage.create_buckets()
    with open('results.xml', 'wb') as output:
        suite = unittest.TestSuite()
        #unittest.main(testRunner=xmlrunner.XMLTestRunner(output=output))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(ProjectTest))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TriggerTest))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(JobApiTest))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(BuildTest))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(JobTest))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(CollaboratorsTest))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TokensTest))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(SecretsTest))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(UserTest))

        testRunner = XMLTestRunner(output=output)
        #unittest.main(testRunner = XMLTestRunner(output=output),
        #              failfast=False, buffer=False, catchbreak=False)
        ret = testRunner.run(suite).wasSuccessful()
        sys.exit(not ret)
