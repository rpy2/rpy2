import unittest
import rpy2.robjects as robjects
rinterface = robjects.rinterface
import array

class RFunctionTestCase(unittest.TestCase):
    def testNew(self):
        identical = rinterface.baseNameSpaceEnv["identical"]
        self.assertRaises(ValueError, robjects.RFunction, 'a')

        ri_f = rinterface.baseNameSpaceEnv.get('help')
        
        ro_f = robjects.RFunction(ri_f)
        
        self.assertTrue(identical(ri_f, ro_f))

    def testCall(self):
        ri_f = rinterface.baseNameSpaceEnv.get('sum')
        ro_f = robjects.RFunction(ri_f)
        
        ro_v = robjects.RVector(array.array('i', [1,2,3]))
        
        s = ro_f(ro_v)

    def testCallWithSexp(self):
        ro_f = robjects.baseNameSpaceEnv["sum"]
        ri_vec = robjects.rinterface.SexpVector([1,2,3], 
                                                robjects.rinterface.INTSXP)
        res = ro_f(ri_vec)
        self.assertEquals(6, res[0])

    def testCallClosureWithRObject(self):
        ri_f = rinterface.baseNameSpaceEnv["sum"]
        ro_vec = robjects.RVector(array.array('i', [1,2,3]))
        res = ri_f(ro_vec)
        self.assertEquals(6, res[0])



def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(RFunctionTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
