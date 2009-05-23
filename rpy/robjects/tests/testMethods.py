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


    def testRS4_TypeNoAccessors(self):
        robjects.r['setClass']("Foo", robjects.r('list(foo="numeric")'))
        class Foo(methods.RS4):
            __metaclass__ = methods.RS4_Type
            def __init__(self):
                obj = robjects.r['new']('R_A')
                self.__sexp__ = obj.__sexp__
        f = Foo()
        

    def testRS4_TypeAccessors(self):
        robjects.r['setClass']("R_A", robjects.r('list(foo="numeric")'))
        robjects.r['setMethod']("length", signature="R_A",
                                definition = robjects.r("function(x) 123"))

        
        class R_A(methods.RS4):
            __metaclass__ = methods.RS4_Type
            __slots__ = ('get_length', 'length')
            __accessors__ = (('length', None,
                              'get_length', False, 'get the length'),
                             ('length', None,
                              None, True, 'length'))
            def __init__(self):
                obj = robjects.r['new']('R_A')
                self.__sexp__ = obj.__sexp__

        class A(R_A):
            __rname__ = 'R_A'


        ra = R_A()
        self.assertEquals(123, ra.get_length()[0])
        self.assertEquals(123, ra.length[0])

        a = A()
        self.assertEquals(123, a.get_length()[0])
        self.assertEquals(123, a.length[0])
        
        
def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(MethodsTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
