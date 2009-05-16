import unittest
import rpy2.rinterface as rinterface
import rpy2.rlike.container as rlc

rinterface.initr()

class SexpClosureTestCase(unittest.TestCase):

    def testNew(self):
        x = "a"
        self.assertRaises(ValueError, rinterface.SexpClosure, x)
        
    def testTypeof(self):
        sexp = rinterface.globalenv.get("plot")
        self.assertEquals(sexp.typeof, rinterface.CLOSXP)

    def testRError(self):
        sum = rinterface.baseenv["sum"]
        letters = rinterface.baseenv["letters"]
        self.assertRaises(rinterface.RRuntimeError, sum, letters)

    def testClosureEnv(self):
        parse = rinterface.baseenv["parse"]
        exp = parse(text = rinterface.SexpVector(["function(x) { x[y] }", ], 
                                                 rinterface.STRSXP))
        fun = rinterface.baseenv["eval"](exp)
        vec = rinterface.baseenv["letters"]
        self.assertRaises(rinterface.RRuntimeError, fun, vec)

        fun.closureEnv()["y"] = rinterface.SexpVector([1, ], 
                                                      rinterface.INTSXP)
        self.assertEquals('a', fun(vec)[0])

        fun.closureEnv()["y"] = rinterface.SexpVector([2, ], 
                                                      rinterface.INTSXP)
        self.assertEquals('b', fun(vec)[0])

    def testCallS4SetClass(self):
        # R's package "methods" can perform uncommon operations
        r_setClass = rinterface.globalenv.get('setClass')
        r_representation = rinterface.globalenv.get('representation')
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
        
        mylist = rinterface.baseenv['list'].rcall(ad.items(), 
                                                           rinterface.globalenv)
        
        names = [x for x in mylist.do_slot("names")]
        
        for i in range(4):
            self.assertEquals(('a', 'b', '', 'c')[i], names[i])

    def testRcallArgsDictEnv(self):
        def parse(x):
            rparse = rinterface.baseenv.get('parse')
            res = rparse(text = rinterface.StrSexpVector((x,)))
            return res
            
        ad = rlc.ArgsDict( ((None, parse('sum(x)')),) )
        env_a = rinterface.baseenv['new.env']()
        env_a['x'] = rinterface.IntSexpVector([1,2,3])
        sum_a = rinterface.baseenv['eval'].rcall(ad.items(), 
                                                          env_a)
        self.assertEquals(6, sum_a[0])
        env_b = rinterface.baseenv['new.env']()
        env_b['x'] = rinterface.IntSexpVector([4,5,6])
        sum_b = rinterface.baseenv['eval'].rcall(ad.items(), 
                                                          env_b)
        self.assertEquals(15, sum_b[0])        
        
    def testErrorInCall(self):
        mylist = rinterface.baseenv['list']
        
        self.assertRaises(ValueError, mylist, 'foo')

    def testMissingArg(self):
        parse = rinterface.baseenv["parse"]
        exp = parse(text=rinterface.SexpVector(["function(x) { missing(x) }"],
                                               rinterface.STRSXP))
        fun = rinterface.baseenv["eval"](exp)
        nonmissing = rinterface.SexpVector([0, ], rinterface.INTSXP)
        missing = rinterface.R_MissingArg
        self.assertEquals(False, fun(nonmissing)[0])
        self.assertEquals(True, fun(missing)[0])

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(SexpClosureTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
