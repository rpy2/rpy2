import unittest

from . import test_ggplot2

def suite():
    suite_ggplot2 = test_ggplot2.suite()
    alltests = unittest.TestSuite([suite_ggplot2, ])
    return alltests
    #pass

def main():
    r = unittest.TestResult()
    suite().run(r)
    return r

if __name__ == '__main__':    
    tr = unittest.TextTestRunner(verbosity = 2)
    suite = suite()
    tr.run(suite)
