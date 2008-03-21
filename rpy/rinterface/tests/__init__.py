import unittest

from . import test_SexpVector
from . import test_SexpEnvironment
from . import test_Sexp

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
