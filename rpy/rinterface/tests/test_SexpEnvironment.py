import unittest
import rpy2.rinterface as rinterface

try:
    #FIXME: can starting and stopping an embedded R be done several times ?
    rinterface.initEmbeddedR("foo", "--vanilla", "--no-save", "--quiet")
except:
    pass

class SexpEnvironmentTestCase(unittest.TestCase):
    #def setUpt(self):
    #    rinterface.initEmbeddedR("foo", "--vanilla", "--no-save")

    #def tearDown(self):
    #    rinterface.endEmbeddedR(0);

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

    def testSubscript(self):
        ge = rinterface.globalEnv
        obj = rinterface.globalEnv.get("letters")
        ge["a"] = obj
        a = rinterface.globalEnv["a"]
        self.assertTrue(False) #FIXME: write proper unit test here

    def testLength(self):
        newEnv = rinterface.globalEnv.get("new.env")
        env = newEnv()
        self.assertEquals(0, len(env))
        env["a"] = rinterface.SexpVector([123, ], rinterface.INTSXP)
        self.assertEquals(1, len(env))
        env["b"] = rinterface.SexpVector([123, ], rinterface.INTSXP)
        self.assertEquals(2, len(env))

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(SexpEnvironmentTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
