import unittest
import rpy2.robjects as robjects
rinterface = robjects.rinterface
import array

class FunctionTestCase(unittest.TestCase):
    def testNew(self):
        identical = rinterface.baseenv["identical"]
        self.assertRaises(ValueError, robjects.Function, 'a')

        ri_f = rinterface.baseenv.get('help')
        
        ro_f = robjects.Function(ri_f)
        
        self.assertTrue(identical(ri_f, ro_f))

    def testCall(self):
        ri_f = rinterface.baseenv.get('sum')
        ro_f = robjects.Function(ri_f)
        
        ro_v = robjects.RVector(array.array('i', [1,2,3]))
        
        s = ro_f(ro_v)

    def testCallWithSexp(self):
        ro_f = robjects.baseenv["sum"]
        ri_vec = robjects.rinterface.SexpVector([1,2,3], 
                                                robjects.rinterface.INTSXP)
        res = ro_f(ri_vec)
        self.assertEquals(6, res[0])

    def testCallClosureWithRObject(self):
        ri_f = rinterface.baseenv["sum"]
        ro_vec = robjects.RVector(array.array('i', [1,2,3]))
        res = ri_f(ro_vec)
        self.assertEquals(6, res[0])

    def testFormals(self):
        ri_f = robjects.r('function(x, y) TRUE')
        res = ri_f.formals()
        #FIXME: no need for as.list when paired list are handled
        res = robjects.r['as.list'](res)
        self.assertEquals(2, len(res))
        n = res.names
        self.assertEquals("x", n[0])
        self.assertEquals("y", n[1])

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(FunctionTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
