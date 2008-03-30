import unittest
import testRobjects

def suite():
    suite_Robjects = testRobjects.suite()
    alltests = unittest.TestSuite([suite_Robjects, ])
    return alltests

def main():
    r = unittest.TestResult()
    suite().run(r)
    return r
