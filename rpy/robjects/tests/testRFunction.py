import unittest
import rpy2.robjects as robjects
rinterface = robjects.rinterface
import array

class RFunctionTestCase(unittest.TestCase):
    def testNew(self):
        self.assertRaises(ValueError, robjects.Rfunction, 'a')

        ri_f = rinterface.baseNameSpaceEnv.get('help')
        
        ro_f = robjects.Rfunction(ri_f)

        #self.assertEquals(ro_v.typeof(), rinterface.INTSXP)
        
        #ri_v = rinterface.SexpVector(py_a)
        #ri_o = rinterface.Sexp(ri_v)
        
        #r_v_new = robject.Rvector(ri_v)
        #r_v_new = robject.Rvector(ro_v)
        
def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(RFunctionTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
