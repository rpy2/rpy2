import unittest
import rpy2.rinterface as rinterface

try:
    #FIXME: can starting and stopping an embedded R be done several times ?
    rinterface.initEmbeddedR()
except:
    pass


class SexpClosureTestCase(unittest.TestCase):
    #def setUpt(self):
    #    rinterface.initEmbeddedR("foo", "--no-save")

    #def tearDown(self):
    #    rinterface.endEmbeddedR(1);

    def testNew(self):
        x = "a"
        self.assertRaises(ValueError, rinterface.SexpClosure, x)
        
    def testTypeof(self):
        sexp = rinterface.globalEnv.get("plot")
        self.assertEquals(sexp.typeof(), rinterface.CLOSXP)

    def testRError(self):
        sum = rinterface.baseNameSpaceEnv["sum"]
        letters = rinterface.baseNameSpaceEnv["letters"]
        self.assertRaises(RuntimeError, sum, letters)

    def testClosureEnv(self):
        parse = rinterface.baseNameSpaceEnv["parse"]
        exp = parse(text = rinterface.SexpVector(["function(x) { x[y] }", ], 
                                                 rinterface.STRSXP))
        fun = rinterface.baseNameSpaceEnv["eval"](exp)
        vec = rinterface.baseNameSpaceEnv["letters"]
        self.assertRaises(RuntimeError, fun, vec)

        fun.closureEnv()["y"] = rinterface.SexpVector([1, ], 
                                                      rinterface.INTSXP)
        self.assertEquals('a', fun(vec)[0])

        fun.closureEnv()["y"] = rinterface.SexpVector([2, ], 
                                                      rinterface.INTSXP)
        self.assertEquals('b', fun(vec)[0])


def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(SexpClosureTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
