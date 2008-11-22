import unittest

import testRObject
import testRVector
import testRArray
import testRDataFrame
import testRFormula
import testRFunction
import testREnvironment
import testRobjects

# wrap this nicely so a warning is issued if no numpy present
import testNumpyConversions

def suite():
    suite_RObject = testRObject.suite()
    suite_RVector = testRVector.suite()
    suite_RArray = testRArray.suite()
    suite_RDataFrame = testRDataFrame.suite()
    suite_RFunction = testRFunction.suite()
    suite_REnvironment = testREnvironment.suite()
    suite_RFormula = testRFormula.suite()
    suite_Robjects = testRobjects.suite()
    suite_NumpyConversions = testNumpyConversions.suite()
    alltests = unittest.TestSuite([suite_RObject,
                                   suite_RVector,                   
                                   suite_RArray,
                                   suite_RDataFrame,
                                   suite_RFunction,
                                   suite_REnvironment,
                                   suite_RFormula,
                                   suite_Robjects,
                                   suite_NumpyConversions
                                   ])
    return alltests

def main():
    r = unittest.TestResult()
    suite().run(r)
    return r
