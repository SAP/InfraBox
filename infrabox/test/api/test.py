import unittest

from xmlrunner import XMLTestRunner

from job_api_test import JobApiTest
from build_test import BuildTest
from job_test import JobTest
from project_test import ProjectTest
from trigger_test import TriggerTest

from pyinfraboxutils.storage import storage



if __name__ == '__main__':
    storage.create_buckets()

    with open('results.xml', 'wb') as output:
        #unittest.main(testRunner=xmlrunner.XMLTestRunner(output=output))
        #project_test_suite = unittest.TestLoader().loadTestsFromTestCase(ProjectTest)
        #trigger_test_suite = unittest.TestLoader().loadTestsFromTestCase(TriggerTest)
        job_api_test_suite = unittest.TestLoader().loadTestsFromTestCase(JobApiTest)
        #build_test_suite = unittest.TestLoader().loadTestsFromTestCase(BuildTest)
        #job_test_suite = unittest.TestLoader().loadTestsFromTestCase(JobTest)

        runner = XMLTestRunner(output=output)
        #runner.run(project_test_suite)
        #runner.run(trigger_test_suite)
        runner.run(job_api_test_suite)
        #runner.run(build_test_suite)
        #runner.run(job_test_suite)
