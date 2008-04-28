import unittest
import rpy2.robjects as robjects
rinterface = robjects.rinterface
import array

class RObjectTestCase(unittest.TestCase):
    def testNew(self):

        identical = rinterface.baseNameSpaceEnv["identical"]
        py_a = array.array('i', [1,2,3])
        self.assertRaises(ValueError, robjects.Robject, py_a)
        
        ri_v = rinterface.SexpVector(py_a, rinterface.INTSXP)
        ro_v = robjects.Robject(ri_v)

        self.assertTrue(identical(ro_v._sexp, ri_v)[0])

        #FIXME: why isn't this working ?
        #del(ri_v)
        self.assertEquals(rinterface.INTSXP, ro_v.typeof())

    def testRepr(self):
        prt = rinterface.baseNameSpaceEnv["print"]
        s = prt.__repr__()

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(RObjectTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
