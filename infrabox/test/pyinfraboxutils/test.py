#! /usr/bin/env python
import unittest
import sys
import xmlrunner

from pyinfraboxutils.coverage import *

class TestCoverageMethods(unittest.TestCase):

    def test_jacoco(self):
        parser = Parser("data/report_test.xml")
        parser.parse(None, create_markup=False)
        self.assertTrue(parser.files[0].functions_found == 2)
        self.assertTrue(parser.files[0].functions_hit == 0)
        self.assertTrue(parser.files[0].branches_found == 2)
        self.assertTrue(parser.files[0].branches_hit == 0)
        self.assertTrue(parser.files[0].lines_hit == 0)
        self.assertTrue(parser.files[0].lines_found == 3)
        self.assertTrue(parser.files[0].name == "HelloWorld.java")

    def test_parse_dir(self):
        parser = Parser("data/")
        parser.parse(None, create_markup=False)

        hello = 0
        hello2 = 1

        if parser.files[0].name == "HelloWorld2.java":
            hello = 1
            hello2 = 0

        self.assertTrue(parser.files[hello].functions_found == 2*2)
        self.assertTrue(parser.files[hello].functions_hit == 0*2)
        self.assertTrue(parser.files[hello].branches_found == 2*2)
        self.assertTrue(parser.files[hello].branches_hit == 0*2)
        self.assertTrue(parser.files[hello].lines_hit == 0*2)
        self.assertTrue(parser.files[hello].lines_found == 3*2)
        self.assertTrue(parser.files[hello].name == "HelloWorld.java")


        self.assertTrue(parser.files[hello2].functions_found == 2)
        self.assertTrue(parser.files[hello2].functions_hit == 0)
        self.assertTrue(parser.files[hello2].branches_found == 2)
        self.assertTrue(parser.files[hello2].branches_hit == 0)
        self.assertTrue(parser.files[hello2].lines_hit == 0)
        self.assertTrue(parser.files[hello2].lines_found == 3)
        self.assertTrue(parser.files[hello2].name == "HelloWorld2.java")

if __name__ == '__main__':
    s = unittest.defaultTestLoader.discover('.')
    r = xmlrunner.XMLTestRunner(output='/infrabox/upload/testresult/').run(s)
    sys.exit(not r.wasSuccessful())
