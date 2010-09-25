import unittest
import rpy2.rinterface as rinterface

rinterface.initr()

class SexpExtPtrTestCase(unittest.TestCase):

    def setUp(self):
        self.console = rinterface.get_writeconsole()
        def noconsole(x):
            pass
        rinterface.set_writeconsole(noconsole)

    def tearDown(self):
        rinterface.set_writeconsole(self.console)

    def testNewDefault(self):
        pyobject = "ahaha"
        sexp_new = rinterface.SexpExtPtr(pyobject)
        # R External pointer are never copied
        self.assertTrue(False) # no real test (yet)

    def testNewTag(self):
        pyobject = "ahaha"
        sexp_new = rinterface.SexpExtPtr(pyobject, 
                                         tag = rinterface.StrSexpVector("b"))
        self.assertTrue(False) # no real test (yet)

    def testNewInvalidTag(self):
        pyobject = "ahaha"
        self.assertRaises(ValueError, rinterface.SexpExtPtr,
                          pyobject, tag = "b")

    def testNewProtected(self):
        pyobject = "ahaha"
        sexp_new = rinterface.SexpExtPtr(pyobject, 
                                         protected = rinterface.StrSexpVector("c"))
        self.assertTrue(False) # no real test (yet)

    def testNewInvalidProtected(self):
        pyobject = "ahaha"
        self.assertRaises(ValueError, rinterface.SexpExtPtr,
                          pyobject, protected = "c")


def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(SexpExtPtrTestCase)
    return suite

if __name__ == '__main__':
    tr = unittest.TextTestRunner(verbosity = 2)
    tr.run(suite())

