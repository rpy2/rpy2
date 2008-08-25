import unittest
import rpy2.rinterface as rinterface
import rpy2.rlike.container as rlc

rinterface.initr()

class SexpClosureTestCase(unittest.TestCase):

    def testNew(self):
        x = "a"
        self.assertRaises(ValueError, rinterface.SexpClosure, x)
        
    def testTypeof(self):
        sexp = rinterface.globalEnv.get("plot")
        self.assertEquals(sexp.typeof, rinterface.CLOSXP)

    def testRError(self):
        sum = rinterface.baseNameSpaceEnv["sum"]
        letters = rinterface.baseNameSpaceEnv["letters"]
        self.assertRaises(rinterface.RRuntimeError, sum, letters)

    def testClosureEnv(self):
        parse = rinterface.baseNameSpaceEnv["parse"]
        exp = parse(text = rinterface.SexpVector(["function(x) { x[y] }", ], 
                                                 rinterface.STRSXP))
        fun = rinterface.baseNameSpaceEnv["eval"](exp)
        vec = rinterface.baseNameSpaceEnv["letters"]
        self.assertRaises(rinterface.RRuntimeError, fun, vec)

        fun.closureEnv()["y"] = rinterface.SexpVector([1, ], 
                                                      rinterface.INTSXP)
        self.assertEquals('a', fun(vec)[0])

        fun.closureEnv()["y"] = rinterface.SexpVector([2, ], 
                                                      rinterface.INTSXP)
        self.assertEquals('b', fun(vec)[0])

    def testCallS4SetClass(self):
        # R's package "methods" can perform uncommon operations
        r_setClass = rinterface.globalEnv.get('setClass')
        r_representation = rinterface.globalEnv.get('representation')
        attrnumeric = rinterface.SexpVector(["numeric", ],
                                            rinterface.STRSXP)
        classname = rinterface.SexpVector(['Track', ], rinterface.STRSXP)
        classrepr = r_representation(x = attrnumeric,
                                     y = attrnumeric)
        r_setClass(classname,
                   classrepr)



    def testRcallArgsDict(self):
        ad = rlc.ArgsDict((('a', rinterface.SexpVector([2, ], 
                                                       rinterface.INTSXP)), 
                           ('b', rinterface.SexpVector([1, ], 
                                                       rinterface.INTSXP)),
                           (None, rinterface.SexpVector([5, ], 
                                                        rinterface.INTSXP)),
                           ('c', rinterface.SexpVector([0, ], 
                                                       rinterface.INTSXP))))
        
        mylist = rinterface.baseNameSpaceEnv['list'].rcall(ad.items())
        
        names = [x for x in mylist.do_slot("names")]
        
        for i in range(4):
            self.assertEquals(('a', 'b', '', 'c')[i], names[i])

    def testErrorInCall(self):
        mylist = rinterface.baseNameSpaceEnv['list']
        
        self.assertRaises(ValueError, mylist, 'foo')


def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(SexpClosureTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
