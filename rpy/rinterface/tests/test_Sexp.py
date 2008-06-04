import unittest
import rpy2.rinterface as rinterface

try:
    #FIXME: can starting and stopping an embedded R be done several times ?
    rinterface.initEmbeddedR()
except:
    pass


class SexpTestCase(unittest.TestCase):
    #def setUpt(self):
    #    rinterface.initEmbeddedR("foo", "--no-save")

    #def tearDown(self):
    #    rinterface.endEmbeddedR(1);

    def testNew_invalid(self):

        x = "a"
        self.assertRaises(ValueError, rinterface.Sexp, x)

    def testNew(self):        
        sexp = rinterface.globalEnv.get("letters")
        sexp_new = rinterface.Sexp(sexp)

        idem = rinterface.globalEnv.get("identical")
        self.assertTrue(idem(sexp, sexp_new)[0])

        sexp_new2 = rinterface.Sexp(sexp)
        self.assertTrue(idem(sexp, sexp_new2)[0])
        del(sexp)
        self.assertTrue(idem(sexp_new, sexp_new2)[0])


    def testTypeof(self):
        sexp = rinterface.globalEnv.get("letters")
        self.assertEquals(sexp.typeof(), rinterface.STRSXP)
        
        sexp = rinterface.globalEnv.get("pi")
        self.assertEquals(sexp.typeof(), rinterface.REALSXP)
        
        sexp = rinterface.globalEnv.get("plot")
        self.assertEquals(sexp.typeof(), rinterface.CLOSXP)

    def testDo_slot(self):
        data_func = rinterface.globalEnv.get("data")
        data_func(rinterface.SexpVector(["iris", ], rinterface.STRSXP))
        sexp = rinterface.globalEnv.get("iris")
        names = sexp.do_slot("names")
        iris_names = ("Sepal.Length", "Sepal.Width", "Petal.Length", "Petal.Width", "Species")

        self.assertEquals(len(iris_names), len(names))

        for i, n in enumerate(iris_names):
            self.assertEquals(iris_names[i], names[i])

        self.assertRaises(LookupError, sexp.do_slot, "foo")       

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(SexpTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
