import unittest

import test_container

def suite():
    suite_container = test_container.suite()
    alltests = unittest.TestSuite([suite_container,
                                   ])
    return alltests

def main():
    r = unittest.TestResult()
    suite().run(r)
    return r
