from tests import *

def run():
    # We want to replace this with a discover call once we clean up rinterface
    alltests = load_tests(unittest.TestLoader(), unittest.TestSuite(),
                          'test*.py')
    unittest.TextTestRunner(verbosity=1).run(alltests)

if __name__ == "__main__":
    import sys, rpy2.rinterface
    sys.stdout.write("rpy2 version: %s\n" % rpy2.__version__)
    sys.stdout.write("built against R version: %s\n" % '-'.join(str(x) for x in rpy2.rinterface.R_VERSION_BUILD))
    sys.stdout.flush()

    run()
