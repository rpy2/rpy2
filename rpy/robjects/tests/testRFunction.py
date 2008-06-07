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


def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(RFunctionTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
