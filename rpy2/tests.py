from os.path import dirname
import unittest

import rpy2
# import rpy2.robjects.tests

# import rpy2.rinterface.tests
# import rpy2.rlike.tests
#import rpy2.interactive.tests

# import rpy2.tests_rpy_classic

def old_load_tests(loader, standard_tests, pattern):
    '''Intercept `python -m unittest discover` run from the module root
    
    Specifically, discover won't look at tests_rpy_classic.py'''
    # A little funny for now while we re-arrange tests a bit
    rpy_root = dirname(rpy2.__file__)

    # suite_robjects = rpy2.robjects.tests.suite()
    # This catches some extra tests (bypassing the suite() functions),
    # at least in a virtualenv that lacks various packages, like numpy,
    # pandas
    suite_robjects = loader.discover('robjects', pattern, rpy_root)
    # suite_rinterface = rpy2.rinterface.tests.load_tests(None, None, None)
    # Raw discovery here loads some stuff that results in a core dump, so
    # we'll retain a load_tests() in rinterface.tests for now.
    suite_rinterface = loader.discover('rinterface', pattern, rpy_root)
    # suite_rlike = rpy2.rlike.tests.suite()
    suite_rlike = loader.discover('rlike', pattern, rpy_root)
    # This was previously disabled
    #suite_interactive = rpy2.interactive.tests.suite()

    # suite_rpy_classic = rpy2.tests_rpy_classic.suite()

    standard_tests.addTests([suite_rinterface,
                             suite_robjects,
                             suite_rlike,
                             #suite_interactive,
                             suite_rpy_classic
                             ])
    return standard_tests

def main():
    # alltests = load_tests(unittest.TestLoader(), unittest.TestSuite(),
    rpy_root = dirname(rpy2.__file__)
    alltests = unittest.defaultTestLoader.discover(rpy2, pattern='test*')
    unittest.TextTestRunner(verbosity=1).run(alltests)

if __name__ == "__main__":
    import sys, rpy2.rinterface
    sys.stdout.write("rpy2 version: %s\n" % rpy2.__version__)
    sys.stdout.write("built against R version: %s\n" % '-'.join(str(x)
        for x in rpy2.rinterface.R_VERSION_BUILD))
    sys.stdout.flush()

    main()
