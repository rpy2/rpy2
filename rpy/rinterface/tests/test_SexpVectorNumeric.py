import unittest
import itertools
import rpy2.rinterface as rinterface
import Numeric


try:
    #FIXME: can starting and stopping an embedded R be done several times ?
    rinterface.initEmbeddedR("foo", "--vanilla", "--no-save", "--quiet")
except:
    pass

def floatEqual(x, y, epsilon = 0.00000001):
    return abs(x - y) < epsilon

class SexpVectorNumericTestCase(unittest.TestCase):

    def testArrayStructInt(self):
        px = [1,-2,3]
        x = rinterface.SexpVector(px, rinterface.INTSXP)
        nx = Numeric.asarray(x)
        self.assertEquals('i', nx.typecode())
        for orig, new in itertools.izip(px, nx):
            self.assertEquals(orig, new)
        self.assertTrue(False)
    
    def testArrayStructDouble(self):
        px = [1.0, -2.0, 3.0]
        x = rinterface.SexpVector(px, rinterface.REALSXP)
        nx = Numeric.asarray(x)
        self.assertEquals('f', nx.typecode())
        for orig, new in itertools.izip(px, nx):
            self.assertEquals(orig, new)
        self.assertTrue(False)

    def testArrayStructComplex(self):
        px = [1+2j, 2+5j, -1+0j]
        x = rinterface.SexpVector(px, rinterface.CPLXSXP)
        nx = Numeric.asarray(x)
        self.assertEquals('D', nx.typecode())
        for orig, new in itertools.izip(px, nx):
            self.assertEquals(orig, new)
        self.assertTrue(False)

#     def testArrayStructBoolean(self):
#         px = [True, False, True]
#         x = rinterface.SexpVector(px, rinterface.REALSXP)
#         nx = Numeric.asarray(x)
#         self.assertEquals('b', nx.typecode())
#         for orig, new in itertools.izip(px, nx):
#             self.assertEquals(orig, new)
#         self.assertTrue(False)

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(SexpVectorNumericTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
