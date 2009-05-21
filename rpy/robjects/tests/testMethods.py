import unittest
import rpy2.robjects as robjects
import rpy2.robjects.methods as methods
rinterface = robjects.rinterface

class MethodsTestCase(unittest.TestCase):
    def testSet_accessors(self):
        robjects.r['setClass']("A")
        robjects.r['setMethod']("length", signature="A",
                                definition = robjects.r("function(x) 123"))
        class A(methods.RS4):
            pass
        acs = (('length', None, True, None), )
        methods.set_accessors(A, "A", None, acs)
        self.assertTrue(False) #FIXME: no unit test
        
def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(MethodsTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
