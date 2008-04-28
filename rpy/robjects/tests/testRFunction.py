import unittest
import rpy2.robjects as robjects
rinterface = robjects.rinterface
import array

class RFunctionTestCase(unittest.TestCase):
    def testNew(self):
        identical = rinterface.baseNameSpaceEnv["identical"]
        self.assertRaises(ValueError, robjects.Rfunction, 'a')

        ri_f = rinterface.baseNameSpaceEnv.get('help')
        
        ro_f = robjects.Rfunction(ri_f)
        
        self.assertTrue(identical(ri_f, ro_f.getSexp()))

    def testCall(self):
        ri_f = rinterface.baseNameSpaceEnv.get('sum')
        ro_f = robjects.Rfunction(ri_f)
        
        ro_v = robjects.Rvector(array.array('i', [1,2,3]))
        
        s = ro_f(ro_v)


def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(RFunctionTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
