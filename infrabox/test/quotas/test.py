#! /usr/bin/env python
import unittest
import sys
import xmlrunner


from pyinfraboxutils import dbpool
from quotas import *


class TestQuotas(unittest.TestCase):
    def check_quotas_db(self):
        db = dbpool.get()

        r = db.execute_one(
            """
            SELECT * FROM public.quotas
            """)
        
        self.assertGreater(r[0] ,0)

    def check_default_value(self):

        self.assertTrue(get_quota_value("max_job_project") == 100)


if __name__ == '__main__':
    s = unittest.defaultTestLoader.discover('.')
    r = xmlrunner.XMLTestRunner(output='/infrabox/upload/testresult/').run(s)
    sys.exit(not r.wasSuccessful())
