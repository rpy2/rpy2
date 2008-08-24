import unittest

import test_SexpVector
import test_SexpEnvironment
import test_Sexp
import test_SexpClosure
import test_SexpVectorNumeric

import test_EmbeddedR
#import test_EmbeddedR_multithreaded


def suite():
    suite_SexpVector = test_SexpVector.suite()
    suite_SexpEnvironment = test_SexpEnvironment.suite()
    suite_Sexp = test_Sexp.suite()
    suite_SexpClosure = test_SexpClosure.suite()
    suite_SexpVectorNumeric = test_SexpVectorNumeric.suite()
    suite_EmbeddedR = test_EmbeddedR.suite()
    #suite_EmbeddedR_multithreaded = test_EmbeddedR_multithreaded.suite()
    alltests = unittest.TestSuite([suite_SexpVector 
                                   ,suite_SexpEnvironment 
                                   ,suite_Sexp
                                   ,suite_SexpClosure
                                   ,suite_SexpVectorNumeric
                                   ,suite_EmbeddedR
    #                               suite_EmbeddedR_multithreaded
                                  ])
    return alltests

def main():
    r = unittest.TestResult()
    suite().run(r)
    return r
