#!/usr/bin/env python

'''tests.py - run all the tests worth running

The goal is that "ERRORS" and "FAILURES" are true failures, and expected
problems sould be dealt with using decorators.'''
from __future__ import print_function

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
    # This now contains a test from IPython
    suite_interactive = loader.discover('interactive', pattern, rpy_root)

    suite_rpy_classic = rpy2.tests_rpy_classic.suite()

    standard_tests.addTests([suite_rinterface,
                             suite_robjects,
                             suite_rlike,
                             suite_interactive,
                             suite_rpy_classic
                             ])
    return standard_tests

def main(verbosity=1):
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
    unittest.TextTestRunner(verbosity=verbosity).run(alltests)

if __name__ == "__main__":
    import sys, rpy2.rinterface
    print("rpy2 version: %s" % rpy2.__version__)
    print("- built against R version: %s" % '-'.join(str(x)
          for x in rpy2.rinterface.R_VERSION_BUILD))

    try:
        import rpy2.rinterface
    except Exception as e:
        print("'rpy2.rinterface' could not be imported:")
        print(e)
        sys.exit(1)
    try:
        rpy2.rinterface.initr()
    except Exception as e:
        print("- The embedded R could not be initialized")
        print(e)
        sys.exit(1)
    try:
        rv = rpy2.rinterface.baseenv['R.version.string']
        print("- running linked to R version: %s" % rv[0])
    except KeyError as ke:
        print("The R version dynamically linked cannot be identified.")
        
    if len(sys.argv) > 1:
        main(verbosity=2)
    else:
        main(verbosity=1)
