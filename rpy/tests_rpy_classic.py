import unittest

import rpy2.rpy_classic as rpy


class RpyClassicTestCase(unittest.TestCase):
    
    def testAttributeExpansion(self):
        rpy.set_default_mode(rpy.BASIC_CONVERSION)
        wtest = rpy.r.wilcox_test
        self.assertTrue(isinstance(wtest, rpy.Robj))

    def testFunctionCall(self):
        rpy.set_default_mode(rpy.BASIC_CONVERSION)
        # positional only
        three = rpy.r.sum(1,2)
        three = three[0] # is this what is happening w/ rpy, or the list is
        # ...automatically dropped ?
        self.assertEquals(3, three)
        # positional + keywords
        onetwothree = rpy.r.seq(1, 3, by=0.5)
        self.assertEquals([1.0, 1.5, 2.0, 2.5, 3.0], onetwothree)

    def testCallable(self):
        rpy.set_default_mode(rpy.NO_CONVERSION)
        #in rpy-1.x, everything is callable
        self.assertTrue(callable(rpy.r.seq))
        self.assertTrue(callable(rpy.r.pi))

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(RpyClassicTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
