import unittest
import rpy2.robjects as robjects
rinterface = robjects.rinterface
import array

class RDataFrameTestCase(unittest.TestCase):

    def testNew(self):
        letters = robjects.r.letters        
        numbers = robjects.r('1:26')
        df = robjects.RDataFrame(letters=letters, numbers=numbers)

        self.assertEquals("data.frame", df.rclass()[0])

    def testDim(self):
        letters = robjects.r.letters        
        numbers = robjects.r('1:26')
        df = robjects.RDataFrame(letters=letters, numbers=numbers)

        self.assertEquals(26, df.nrow())
        self.assertEquals(2, df.ncol())


def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(RDataFrameTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
