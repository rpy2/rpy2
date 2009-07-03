import unittest

import testRObject
import testRVector
import testRArray
import testDataFrame
import testFormula
import testRFunction
import testREnvironment
import testRobjects
import testMethods

# wrap this nicely so a warning is issued if no numpy present
import testNumpyConversions

def suite():
    suite_RObject = testRObject.suite()
    suite_RVector = testRVector.suite()
    suite_RArray = testRArray.suite()
    suite_DataFrame = testDataFrame.suite()
    suite_RFunction = testRFunction.suite()
    suite_REnvironment = testREnvironment.suite()
    suite_Formula = testFormula.suite()
    suite_Robjects = testRobjects.suite()
    suite_NumpyConversions = testNumpyConversions.suite()
    suite_Methods = testMethods.suite()
    alltests = unittest.TestSuite([suite_RObject,
                                   suite_RVector,                   
                                   suite_RArray,
                                   suite_DataFrame,
                                   suite_RFunction,
                                   suite_REnvironment,
                                   suite_Formula,
                                   suite_Robjects,
                                   suite_Methods,
                                   suite_NumpyConversions
                                   ])
    return alltests

def main():
    r = unittest.TestResult()
    suite().run(r)
    return r
