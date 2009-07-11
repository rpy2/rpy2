import unittest
import rpy2.robjects as robjects
rinterface = robjects.rinterface
import array

class ArrayTestCase(unittest.TestCase):

    def testNew(self):
        letters = robjects.r.letters        
        self.assertRaises(TypeError, robjects.Array, letters)
        m = robjects.r.matrix(1, nrow=5, ncol=3)
        a = robjects.Array(m)
        # only tests that it runs.

    def testDim(self):
        m = robjects.r.matrix(1, nrow=5, ncol=3)
        a = robjects.Array(m)
        d = a.dim
        self.assertEquals(2, len(d))
        self.assertEquals(5, d[0])
        self.assertEquals(3, d[1])

#         rd = robjects.r.rev(d)
#         a.dim = rd


    def testNamesGet(self):
        dimnames = robjects.r.list(robjects.StrVector(['a', 'b', 'c']),
                                   robjects.StrVector(['d', 'e']))
        m = robjects.r.matrix(1, nrow=3, ncol=2,
                              dimnames = dimnames)
        a = robjects.Array(m)
        res = a.names
        r_identical = robjects.r.identical
        self.assertTrue(r_identical(dimnames[0], res[0]))
        self.assertTrue(r_identical(dimnames[1], res[1]))

    def testNamesSet(self):
        dimnames = robjects.r.list(robjects.StrVector(['a', 'b', 'c']),
                                   robjects.StrVector(['d', 'e']))
        m = robjects.r.matrix(1, nrow=3, ncol=2)
        a = robjects.Array(m)
        a.names = dimnames
        res = a.names
        r_identical = robjects.r.identical
        self.assertTrue(r_identical(dimnames[0], res[0]))
        self.assertTrue(r_identical(dimnames[1], res[1]))

class MatrixTestCase(unittest.TestCase):

    def testNrowGet(self):
        m = robjects.r.matrix(robjects.IntVector(range(6)), nrow=3, ncol=2)
        self.assertEquals(3, m.nrow)

    def testNcolGet(self):
        m = robjects.r.matrix(robjects.IntVector(range(6)), nrow=3, ncol=2)
        self.assertEquals(2, m.ncol)

    def testTranspose(self):
        m = robjects.r.matrix(robjects.IntVector(range(6)), nrow=3, ncol=2)
        mt = m.transpose()
        for i in (0,1,2,3,4,5,):
            self.assertEquals(i, m[i])
        for i in (0,3,1,4,2,5):
            self.assertEquals(i, mt[i])

    def testCrossprod(self):
        self.assertTrue(False)  # no test yet
    def testTCrossprod(self):
        self.assertTrue(False)  # no test yet
    def testSVD(self):
        self.assertTrue(False) # no test yet
    def testEigen(self):
        self.assertTrue(False) # no test yet
    def testDot(self):
        m = robjects.r.matrix(robjects.IntVector(range(4)), nrow=2, ncol=2)        
        m2 = m.dot(m)
        self.assertEquals((2,3,6,11), tuple(m2))

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(ArrayTestCase)
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(MatrixTestCase))
    return suite

if __name__ == '__main__':
     unittest.main()
