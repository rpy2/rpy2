import unittest
import itertools
import rpy2.rinterface as rinterface


try:
    import numpy
    has_Numpy = True
except ImportError:
    hasNumpy = False


rinterface.initr()

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
    
def testArrayStructBoolean(self, numericModule):
    px = [True, False, True]
    x = rinterface.SexpVector(px, rinterface.LGLSXP)
    nx = numericModule.asarray(x)
    self.assertEquals('i', nx.dtype.kind) # not 'b', see comments in array.c
    for orig, new in itertools.izip(px, nx):
        self.assertEquals(orig, new)


class SexpVectorNumericTestCase(unittest.TestCase):


    def testArrayStructNumpyInt(self):
        testArrayStructInt(self, numpy)

    def testArrayStructNumpyDouble(self):
        testArrayStructDouble(self, numpy)

    def testArrayStructNumpyComplex(self):
        testArrayStructComplex(self, numpy)

    def testArrayStructNumpyBoolean(self):
        testArrayStructBoolean(self, numpy)

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(SexpVectorNumericTestCase)
    return suite

if __name__ == '__main__':
    tr = unittest.TextTestRunner(verbosity = 2)
    tr.run(suite())

