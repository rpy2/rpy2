import unittest
import rpy2.robjects as robjects
rinterface = robjects.rinterface
import array

class RObjectTestCase(unittest.TestCase):
    def testNew(self):

        identical = rinterface.baseNameSpaceEnv["identical"]
        py_a = array.array('i', [1,2,3])
        self.assertRaises(ValueError, robjects.RObject, py_a)
        
        ri_v = rinterface.SexpVector(py_a, rinterface.INTSXP)
        ro_v = robjects.RObject(ri_v)

        self.assertTrue(identical(ro_v, ri_v)[0])

        del(ri_v)
        self.assertEquals(rinterface.INTSXP, ro_v.typeof)

    def testR_repr(self):
        obj = robjects.baseNameSpaceEnv["pi"]
        s = obj.r_repr()
        self.assertTrue(s.startswith('3.14'))


    def testStr(self):
        prt = robjects.baseNameSpaceEnv["pi"]
        s = prt.__str__()
        self.assertTrue(s.startswith('[1] 3.14'))


    def testRclass(self):
        self.assertEquals("character",
                          robjects.baseNameSpaceEnv["letters"].rclass[0])
        self.assertEquals("numeric",
                          robjects.baseNameSpaceEnv["pi"].rclass[0])
        self.assertEquals("function",
                          robjects.globalEnv.get("help").rclass[0])

    def testDo_slot(self):
        self.assertEquals("A1.4, p. 270",
                          robjects.globalEnv.get("BOD").do_slot("reference")[0])


def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(RObjectTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
