import unittest
import rpy2.robjects as robjects
rinterface = robjects.rinterface
import array

class RArrayTestCase(unittest.TestCase):

    def testNew(self):
        letters = robjects.r.letters        
        self.assertRaises(TypeError, robjects.RArray, letters)
        m = robjects.r.matrix(1, nrow=5, ncol=3)
        a = robjects.RArray(m)
        # only tests that it runs.

    def testDim(self):
        m = robjects.r.matrix(1, nrow=5, ncol=3)
        a = robjects.RArray(m)
        d = a.dim
        self.assertEquals(2, len(d))
        self.assertEquals(5, d[0])
        self.assertEquals(3, d[1])



def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(RArrayTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
