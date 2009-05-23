import unittest
import rpy2.robjects as robjects
import rpy2.robjects.methods as methods
rinterface = robjects.rinterface

class MethodsTestCase(unittest.TestCase):
    def testSet_accessors(self):
        robjects.r['setClass']("A", robjects.r('list(foo="numeric")'))
        robjects.r['setMethod']("length", signature="A",
                                definition = robjects.r("function(x) 123"))
        class A(methods.RS4):
            def __init__(self):
                obj = robjects.r['new']('A')
                self.__sexp__ = obj.__sexp__

        acs = (('length', None, True, None), )
        methods.set_accessors(A, "A", None, acs)
        a = A()
        self.assertEquals(123, a.length[0])


    def testRS4_TypeAccessors(self):
        robjects.r['setClass']("A", robjects.r('list(foo="numeric")'))
        robjects.r['setMethod']("length", signature="A",
                                definition = robjects.r("function(x) 123"))
        class A(methods.RS4):
            __metaclass__ = methods.RS4_Type
            __rname__ = 'A'
            __slots__ = ('get_length', 'length')
            __accessors__ = (('length', None,
                              'get_length', False, 'get the length'),
                             ('length', None,
                              'length', True, 'length'))
            def __init__(self):
                obj = robjects.r['new']('A')
                self.__sexp__ = obj.__sexp__
                
        a = A()
        #import pdb; pdb.set_trace()
        self.assertEquals(123, a.get_length()[0])
        self.assertEquals(123, a.length[0])
        
        
def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(MethodsTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
