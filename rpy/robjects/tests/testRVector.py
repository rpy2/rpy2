import unittest
import rpy2.robjects as robjects
rinterface = robjects.rinterface
import array

class RvectorTestCase(unittest.TestCase):
    def testNew(self):
        py_a = array.array('i', [1,2,3])
        ro_v = robjects.Rvector(py_a)
        self.assertEquals(ro_v.typeof(), rinterface.INTSXP)
        
        ri_v = rinterface.SexpVector(py_a)
        
        #r_v_new = robject.Rvector(ri_v)
        #r_v_new = robject.Rvector(ro_v)
        
def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(RvectorTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
