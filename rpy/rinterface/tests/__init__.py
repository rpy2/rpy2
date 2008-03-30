import unittest

import test_SexpVector
import test_SexpEnvironment
import test_Sexp

def suite():
    suite_SexpVector = test_SexpVector.suite()
    suite_SexpEnvironment = test_SexpEnvironment.suite()
    suite_Sexp = test_Sexp.suite()
    alltests = unittest.TestSuite([suite_SexpVector, suite_SexpEnvironment, suite_Sexp])
    return alltests

def main():
    r = unittest.TestResult()
    suite().run(r)
    return r
