import unittest
import itertools
import rpy2.rinterface as rinterface


try:
    import numpy
    has_Numpy = True
except ImportError:
    hasNumpy = False


try:
    #FIXME: can starting and stopping an embedded R be done several times ?
    rinterface.initEmbeddedR()
except:
    pass

def floatEqual(x, y, epsilon = 0.00000001):
    return abs(x - y) < epsilon

def testArrayStructInt(self, numericModule):
    px = [1, -2, 3]
    x = rinterface.SexpVector(px, rinterface.INTSXP)
    nx = numericModule.asarray(x)
    self.assertEquals(nx.dtype.kind, 'i')
    for orig, new in itertools.izip(px, nx):
        self.assertEquals(orig, new)

    # change value in the Python array... makes it change in the R vector
    nx[1] = 12
    self.assertEquals(x[1], 12)

def testArrayStructDouble(self, numericModule):
    px = [1.0, -2.0, 3.0]
    x = rinterface.SexpVector(px, rinterface.REALSXP)
    nx = numericModule.asarray(x)
    self.assertEquals(nx.dtype.kind, 'f')
    for orig, new in itertools.izip(px, nx):
        self.assertEquals(orig, new)
    
    # change value in the Python array... makes it change in the R vector
    nx[1] = 333.2
    self.assertEquals(x[1], 333.2)

def testArrayStructComplex(self, numericModule):
    px = [1+2j, 2+5j, -1+0j]
    x = rinterface.SexpVector(px, rinterface.CPLXSXP)
    nx = numericModule.asarray(x)
    self.assertEquals(nx.dtype.kind, 'c')
    for orig, new in itertools.izip(px, nx):
        self.assertEquals(orig, new)
    

class SexpVectorNumericTestCase(unittest.TestCase):


    def testArrayStructNumpyInt(self):
        testArrayStructInt(self, numpy)

    def testArrayStructNumpyDouble(self):
        testArrayStructDouble(self, numpy)

    def testArrayStructNumpyComplex(self):
        testArrayStructComplex(self, numpy)



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
