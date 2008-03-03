import unittest
import rinterface

#FIXME: can starting and stopping an embedded R be done several times ?
rinterface.initEmbeddedR("foo", "--vanilla", "--no-save", "--quiet")

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

if __name__ == '__main__':
     unittest.main()
