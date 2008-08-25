import unittest
import rpy2.rinterface as rinterface

rinterface.initr()

class SexpTestCase(unittest.TestCase):

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


    def testTypeof_get(self):
        sexp = rinterface.globalEnv.get("letters")
        self.assertEquals(sexp.typeof, rinterface.STRSXP)
        
        sexp = rinterface.globalEnv.get("pi")
        self.assertEquals(sexp.typeof, rinterface.REALSXP)
        
        sexp = rinterface.globalEnv.get("plot")
        self.assertEquals(sexp.typeof, rinterface.CLOSXP)

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

    def testDo_slot_assign(self):
        data_func = rinterface.globalEnv.get("data")
        data_func(rinterface.SexpVector(["iris", ], rinterface.STRSXP))
        sexp = rinterface.globalEnv.get("iris")
        iris_names = rinterface.StrSexpVector(['a', 'b', 'c', 'd', 'e'])
        sexp.do_slot_assign("names", iris_names)
        names = [x for x in sexp.do_slot("names")]
        self.assertEquals(['a', 'b', 'c', 'd', 'e'], names)

    def testSexp_rsame_true(self):
        sexp_a = rinterface.globalEnv.get("letters")
        sexp_b = rinterface.globalEnv.get("letters")
        self.assertTrue(sexp_a.rsame(sexp_b))

    def testSexp_rsame_false(self):
        sexp_a = rinterface.globalEnv.get("letters")
        sexp_b = rinterface.globalEnv.get("pi")
        self.assertFalse(sexp_a.rsame(sexp_b))

    def testSexp_rsame_wrongType(self):
        sexp_a = rinterface.globalEnv.get("letters")
        self.assertRaises(ValueError, sexp_a.rsame, 'foo')
        

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(SexpTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
