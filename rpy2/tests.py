#!/usr/bin/env python

'''tests.py - run all the tests worth running

The goal is that "ERRORS" and "FAILURES" are true failures, and expected
problems sould be dealt with using decorators.'''

from os.path import dirname
import unittest

import rpy2
import rpy2.tests_rpy_classic

def faster_load_tests(loader, standard_tests, pattern):
    '''Run tests a little faster than TestLoader.discover()'''
    # A little funny for now while we re-arrange tests a bit
    rpy_root = dirname(rpy2.__file__)

    # This now catches some extra tests (bypassing the suite() functions),
    # at least in a virtualenv that lacks various packages, like numpy &
    # pandas
    suite_robjects = loader.discover('robjects', pattern, rpy_root)
    suite_rinterface = loader.discover('rinterface', pattern, rpy_root)
    suite_rlike = loader.discover('rlike', pattern, rpy_root)

    # This contains no functional tests
    #suite_interactive = rpy2.interactive.tests.suite()

    suite_rpy_classic = rpy2.tests_rpy_classic.suite()

    standard_tests.addTests([suite_rinterface,
                             suite_robjects,
                             suite_rlike,
                             #suite_interactive,
                             suite_rpy_classic
                             ])
    return standard_tests

def main():
    # For some reason, the commented code is slow and loads some things twice
    # One specific message is regarding package_dependencies from the tools
    # package.
    # rpy_root = dirname(rpy2.__file__)
    # alltests = unittest.defaultTestLoader.discover(rpy2, pattern='test*')

    # This is still pretty generic and requires very little maintenence (except
    # for the robjects.tests.load_tests() function, which is still coded by hand
    alltests = faster_load_tests(unittest.defaultTestLoader,
                                 unittest.TestSuite(),
                                 'test*')
    unittest.TextTestRunner(verbosity=1).run(alltests)

if __name__ == "__main__":
    import sys, rpy2.rinterface
    sys.stdout.write("rpy2 version: %s\n" % rpy2.__version__)
    sys.stdout.write("built against R version: %s\n" % '-'.join(str(x)
        for x in rpy2.rinterface.R_VERSION_BUILD))
    sys.stdout.flush()

    main()
