import unittest
import copy
import gc
import rpy2.rinterface as rinterface

rinterface.initr()

class SexpTestCase(unittest.TestCase):

    def testNew_invalid(self):

        x = "a"
        self.assertRaises(ValueError, rinterface.Sexp, x)

    def testNew(self):
        sexp = rinterface.baseenv.get("letters")
        sexp_new = rinterface.Sexp(sexp)

        idem = rinterface.baseenv.get("identical")
        self.assertTrue(idem(sexp, sexp_new)[0])

        sexp_new2 = rinterface.Sexp(sexp)
        self.assertTrue(idem(sexp, sexp_new2)[0])
        del(sexp)
        self.assertTrue(idem(sexp_new, sexp_new2)[0])


    def testTypeof_get(self):
        sexp = rinterface.baseenv.get("letters")
        self.assertEquals(sexp.typeof, rinterface.STRSXP)
        
        sexp = rinterface.baseenv.get("pi")
        self.assertEquals(sexp.typeof, rinterface.REALSXP)
        
        sexp = rinterface.baseenv.get("plot")
        self.assertEquals(sexp.typeof, rinterface.CLOSXP)

    def testDo_slot(self):
        data_func = rinterface.baseenv.get("data")
        data_func(rinterface.SexpVector(["iris", ], rinterface.STRSXP))
        sexp = rinterface.globalenv.get("iris")
        names = sexp.do_slot("names")
        iris_names = ("Sepal.Length", "Sepal.Width", "Petal.Length", "Petal.Width", "Species")

        self.assertEquals(len(iris_names), len(names))

        for i, n in enumerate(iris_names):
            self.assertEquals(iris_names[i], names[i])

        self.assertRaises(LookupError, sexp.do_slot, "foo")  

    def testDo_slot_assign(self):
        data_func = rinterface.baseenv.get("data")
        data_func(rinterface.SexpVector(["iris", ], rinterface.STRSXP))
        sexp = rinterface.globalenv.get("iris")
        iris_names = rinterface.StrSexpVector(['a', 'b', 'c', 'd', 'e'])
        sexp.do_slot_assign("names", iris_names)
        names = [x for x in sexp.do_slot("names")]
        self.assertEquals(['a', 'b', 'c', 'd', 'e'], names)

    def testDo_slot_assign_create(self):
        #test that assigning slots is also creating the slot
        x = rinterface.IntSexpVector([1,2,3])
        x.do_slot_assign("foo", rinterface.StrSexpVector(["bar", ]))
        slot = x.do_slot("foo")
        self.assertEquals(1, len(slot))
        self.assertEquals("bar", slot[0])

    def testSexp_rsame_true(self):
        sexp_a = rinterface.baseenv.get("letters")
        sexp_b = rinterface.baseenv.get("letters")
        self.assertTrue(sexp_a.rsame(sexp_b))

    def testSexp_rsame_false(self):
        sexp_a = rinterface.baseenv.get("letters")
        sexp_b = rinterface.baseenv.get("pi")
        self.assertFalse(sexp_a.rsame(sexp_b))

    def testSexp_rsame_wrongType(self):
        sexp_a = rinterface.baseenv.get("letters")
        self.assertRaises(ValueError, sexp_a.rsame, 'foo')

    def testSexp_sexp(self):
        sexp = rinterface.IntSexpVector([1,2,3])
        cobj = sexp.__sexp__
        sexp = rinterface.IntSexpVector([4,5,6,7])
        self.assertEquals(4, len(sexp))
        sexp.__sexp__ = cobj
        self.assertEquals(3, len(sexp))

    def testSexp_sexp_wrongtypeof(self):
        sexp = rinterface.IntSexpVector([1,2,3])
        cobj = sexp.__sexp__
        sexp = rinterface.StrSexpVector(['a', 'b'])
        self.assertEquals(2, len(sexp))
        self.assertRaises(ValueError, sexp.__setattr__, '__sexp__', cobj)


    def testSexp_sexp_destroyCobj(self):
        sexp = rinterface.IntSexpVector([1,2,3])
        cobj = sexp.__sexp__
        del(cobj)
        gc.collect()
        # no real test, just make sure that it does
        # not cause a segfault

        
    def testSexp_deepcopy(self):
        sexp = rinterface.IntSexpVector([1,2,3])
        self.assertEquals(0, sexp.named)
        rinterface.baseenv.get("identity")(sexp)
        self.assertEquals(2, sexp.named)
        sexp2 = sexp.__deepcopy__()
        self.assertEquals(sexp.typeof, sexp2.typeof)
        self.assertEquals(list(sexp), list(sexp2))
        self.assertFalse(sexp.rsame(sexp2))
        self.assertEquals(0, sexp2.named)
        # should be the same as above, but just in case:
        sexp3 = copy.deepcopy(sexp)
        self.assertEquals(sexp.typeof, sexp3.typeof)
        self.assertEquals(list(sexp), list(sexp3))
        self.assertFalse(sexp.rsame(sexp3))
        self.assertEquals(0, sexp3.named)

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(SexpTestCase)
    return suite

if __name__ == '__main__':
    tr = unittest.TextTestRunner(verbosity = 2)
    tr.run(suite())
