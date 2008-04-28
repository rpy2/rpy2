import unittest

import testRObject
import testRVector
import testRFunction
import testREnvironment
import testRobjects

def suite():
    suite_RObject = testRObject.suite()
    suite_RVector = testRVector.suite()
    suite_RFunction = testRFunction.suite()
    suite_REnvironment = testREnvironment.suite()
    suite_Robjects = testRobjects.suite()
    alltests = unittest.TestSuite([suite_RObject,
                                   suite_RVector,
                                   suite_RFunction,
                                   suite_REnvironment,
                                   suite_Robjects ])
    return alltests

def main():
    r = unittest.TestResult()
    suite().run(r)
    return r
