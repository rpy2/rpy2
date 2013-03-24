from os.path import dirname, join
import unittest

import rpy2
# import rpy2.robjects.tests

import rpy2.rinterface.tests
# import rpy2.rlike.tests
#import rpy2.interactive.tests

import rpy2.tests.tests_rpy_classic

def load_tests(loader, standard_tests, pattern):
    '''Intercept `python -m unittest discover` run from the module root
    
    Specifically, discover won't look at tests_rpy_classic.py'''
    # A little funny for now while we re-arrange tests a bit
    rpy_root = dirname(rpy2.__file__)

    # suite_robjects = rpy2.robjects.tests.suite()
    # This catches some extra tests (bypassing the suite() functions),
    # at least in a virtualenv that lacks various packages, like numpy,
    # pandas
    suite_robjects = loader.discover('robjects', pattern, rpy_root)
    suite_rinterface = rpy2.rinterface.tests.suite()
    # This loads some stuff that results in a core dump
    # suite_rinterface = loader.discover('rinterface/tests', pattern, this_dir)
    # suite_rlike = rpy2.rlike.tests.suite()
    suite_rlike = loader.discover('rlike', pattern, rpy_root)
    #suite_interactive = rpy2.interactive.tests.suite()

    suite_rpy_classic = rpy2.tests.tests_rpy_classic.suite()

    standard_tests.addTests([suite_rinterface,
                             suite_robjects,
                             suite_rlike,
                             #suite_interactive,
                             suite_rpy_classic
                             ])
    return standard_tests


if __name__ == "__main__":
    alltests = load_tests(unittest.TestLoader(), unittest.TestSuite(),
                          'test*.py')
    unittest.TextTestRunner(verbosity=1).run(alltests)
