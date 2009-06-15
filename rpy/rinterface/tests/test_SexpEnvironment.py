import unittest
import rpy2.rinterface as rinterface

rinterface.initr()

class SexpEnvironmentTestCase(unittest.TestCase):

    def testNew(self):
        sexp = rinterface.globalEnv
        sexp_new = rinterface.SexpEnvironment(sexp)

        idem = rinterface.globalEnv.get("identical")
        self.assertTrue(idem(sexp, sexp_new)[0])

        sexp_new2 = rinterface.Sexp(sexp)
        self.assertTrue(idem(sexp, sexp_new2)[0])
        del(sexp)
        self.assertTrue(idem(sexp_new, sexp_new2)[0])

        self.assertRaises(ValueError, rinterface.SexpEnvironment, '2')

    def testGlobalEnv(self):
        ok = isinstance(rinterface.globalEnv, rinterface.SexpEnvironment) 
        self.assertTrue(ok)

    def testGet(self):
        help_R = rinterface.globalEnv.get("help")
        ok = isinstance(help_R, rinterface.SexpClosure)
        self.assertTrue(ok)

        pi_R = rinterface.globalEnv.get("pi")
        ok = isinstance(pi_R, rinterface.SexpVector)
        self.assertTrue(ok)

        ge_R = rinterface.globalEnv.get(".GlobalEnv")
        ok = isinstance(ge_R, rinterface.SexpEnvironment)
        self.assertTrue(ok)

        self.assertRaises(LookupError, rinterface.globalEnv.get, "survfit")
        rinterface.globalEnv.get("library")(rinterface.SexpVector(["survival", ],
                                            rinterface.STRSXP))
        sfit_R = rinterface.globalEnv.get("survfit")
        ok = isinstance(sfit_R, rinterface.SexpClosure)
        self.assertTrue(ok)

    def testGetEmptyString(self):
        self.assertRaises(ValueError, rinterface.globalEnv.get, "")

    def testGet_functionOnly_lookupError(self):
        # now with the function-only option

        self.assertRaises(LookupError, 
                          rinterface.globalEnv.get, "pi", wantFun = True)

    def testGet_functionOnly(self):
        hist = rinterface.globalEnv.get("hist", wantFun = False)
        self.assertEquals(rinterface.CLOSXP, hist.typeof)
        rinterface.globalEnv["hist"] = rinterface.SexpVector(["foo", ], 
                                                             rinterface.STRSXP)

        hist = rinterface.globalEnv.get("hist", wantFun = True)
        self.assertEquals(rinterface.CLOSXP, hist.typeof)
        

    def testSubscript(self):
        ge = rinterface.globalEnv
        obj = rinterface.globalEnv.get("letters")
        ge["a"] = obj
        a = rinterface.globalEnv["a"]
        ok = ge.get("identical")(obj, a)
        self.assertTrue(ok[0])

    def testSubscriptEmptyString(self):
        self.assertRaises(ValueError, rinterface.globalEnv.__getitem__, "")

    def testLength(self):
        newEnv = rinterface.globalEnv.get("new.env")
        env = newEnv()
        self.assertEquals(0, len(env))
        env["a"] = rinterface.SexpVector([123, ], rinterface.INTSXP)
        self.assertEquals(1, len(env))
        env["b"] = rinterface.SexpVector([123, ], rinterface.INTSXP)
        self.assertEquals(2, len(env))

    def testIter(self):
        newEnv = rinterface.globalEnv.get("new.env")
        env = newEnv()
        env["a"] = rinterface.SexpVector([123, ], rinterface.INTSXP)
        env["b"] = rinterface.SexpVector([456, ], rinterface.INTSXP)
        symbols = [x for x in env]
        self.assertEquals(2, len(symbols))
        for s in ["a", "b"]:
            self.assertTrue(s in symbols)

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(SexpEnvironmentTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
