import unittest

import testRObject
import testRVector
import testArray
import testDataFrame
import testFormula
import testRFunction
import testEnvironment
import testRobjects
import testMethods
import testPackages

# wrap this nicely so a warning is issued if no numpy present
import testNumpyConversions

def suite():
    suite_RObject = testRObject.suite()
    suite_RVector = testRVector.suite()
    suite_Array = testArray.suite()
    suite_DataFrame = testDataFrame.suite()
    suite_RFunction = testRFunction.suite()
    suite_Environment = testEnvironment.suite()
    suite_Formula = testFormula.suite()
    suite_Robjects = testRobjects.suite()
    suite_NumpyConversions = testNumpyConversions.suite()
    suite_Methods = testMethods.suite()
    suite_Packages = testPackages.suite()
    alltests = unittest.TestSuite([suite_RObject,
                                   suite_RVector,                   
                                   suite_Array,
                                   suite_DataFrame,
                                   suite_RFunction,
                                   suite_Environment,
                                   suite_Formula,
                                   suite_Robjects,
                                   suite_Methods,
                                   suite_NumpyConversions,
                                   suite_Packages
                                   ])
    return alltests

def main():
    r = unittest.TestResult()
    suite().run(r)
    return r
