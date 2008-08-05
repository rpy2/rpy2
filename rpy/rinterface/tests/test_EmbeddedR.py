import unittest
import rpy2.rinterface as rinterface

rinterface.initEmbeddedR()

class EmbeddedRTestCase(unittest.TestCase):
    def testSetWriteConsole(self):
        buf = []
        def f(x):
            buf.append(x)

        rinterface.setWriteConsole(f)
        code = rinterface.SexpVector(["3", ], rinterface.STRSXP)
        rinterface.baseNameSpaceEnv["print"](code)
        self.assertEquals('[1] "3"\n', str.join('', buf))
        rinterface.setWriteConsole(rinterface.consolePrint)

    def testSetReadConsole(self):
        yes = "yes\n"
        def sayyes(prompt):
            return(yes)
        rinterface.setReadConsole(sayyes)
        res = rinterface.baseNameSpaceEnv["readline"]()
        self.assertEquals(yes.strip(), res[0])
        rinterface.setReadConsole(rinterface.consoleRead)

    def testCallErrorWhenEndedR(self):
        t = rinterface.baseNameSpaceEnv['date']
        rinterface.endEmbeddedR(1)
        self.assertRaises(RuntimeError, t)
        rinterface.initEmbeddedR()


class ObjectDispatchTestCase(unittest.TestCase):
    def testObjectDispatchLang(self):
        formula = rinterface.globalEnv.get('formula')
        obj = formula(rinterface.StrSexpVector(['y ~ x', ]))
        self.assertTrue(isinstance(obj, rinterface.SexpLang))

    def testObjectDispatchVector(self):
        letters = rinterface.globalEnv.get('letters')
        self.assertTrue(isinstance(letters, rinterface.SexpVector))

    def testObjectDispatchClosure(self):
        #import pdb; pdb.set_trace()
        help = rinterface.globalEnv.get('sum')
        self.assertTrue(isinstance(help, rinterface.SexpClosure))

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(EmbeddedRTestCase)
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(ObjectDispatchTestCase))
    return suite

if __name__ == '__main__':
     unittest.main()
