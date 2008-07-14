import unittest

import rpy2.robjects.tests
import rpy2.rinterface.tests
import rpy2.rlike.tests

def suite():
    suite_robjects = rpy2.robjects.tests.suite()
    suite_rinterface = rpy2.rinterface.tests.suite()
    suite_rlike = rpy2.rlike.tests.suite()
    alltests = unittest.TestSuite([suite_robjects, 
                                   suite_rinterface, 
                                   suite_rlike])
    return alltests

if __name__ == "__main__":
    unittest.main(defaultTest = "suite")

