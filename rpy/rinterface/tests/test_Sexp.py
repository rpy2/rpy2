import unittest
import copy
import gc
from rpy2 import rinterface

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
        self.assertEqual(sexp.typeof, rinterface.STRSXP)
        
        sexp = rinterface.baseenv.get("pi")
        self.assertEqual(sexp.typeof, rinterface.REALSXP)
        
        sexp = rinterface.baseenv.get("plot")
        self.assertEqual(sexp.typeof, rinterface.CLOSXP)

    def testList_attrs(self):
        x = rinterface.IntSexpVector((1,2,3))
        self.assertEqual(0, len(x.list_attrs()))
        x.do_slot_assign('a', rinterface.IntSexpVector((33,)))
        self.assertEqual(1, len(x.list_attrs()))
        self.assertTrue('a' in x.list_attrs())

    def testDo_slot(self):
        data_func = rinterface.baseenv.get("data")
        data_func(rinterface.SexpVector(["iris", ], rinterface.STRSXP))
        sexp = rinterface.globalenv.get("iris")
        names = sexp.do_slot("names")
        iris_names = ("Sepal.Length", "Sepal.Width", "Petal.Length", "Petal.Width", "Species")

        self.assertEqual(len(iris_names), len(names))

        for i, n in enumerate(iris_names):
            self.assertEqual(iris_names[i], names[i])

        self.assertRaises(LookupError, sexp.do_slot, "foo")  

    def testDo_slot_assign(self):
        data_func = rinterface.baseenv.get("data")
        data_func(rinterface.SexpVector(["iris", ], rinterface.STRSXP))
        sexp = rinterface.globalenv.get("iris")
        iris_names = rinterface.StrSexpVector(['a', 'b', 'c', 'd', 'e'])
        sexp.do_slot_assign("names", iris_names)
        names = [x for x in sexp.do_slot("names")]
        self.assertEqual(['a', 'b', 'c', 'd', 'e'], names)

    def testDo_slot_assign_create(self):
        #test that assigning slots is also creating the slot
        x = rinterface.IntSexpVector([1,2,3])
        x.do_slot_assign("foo", rinterface.StrSexpVector(["bar", ]))
        slot = x.do_slot("foo")
        self.assertEqual(1, len(slot))
        self.assertEqual("bar", slot[0])

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
        self.assertEqual(4, len(sexp))
        sexp.__sexp__ = cobj
        self.assertEqual(3, len(sexp))

    def testSexp_sexp_wrongtypeof(self):
        sexp = rinterface.IntSexpVector([1,2,3])
        cobj = sexp.__sexp__
        sexp = rinterface.StrSexpVector(['a', 'b'])
        self.assertEqual(2, len(sexp))
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
        self.assertEqual(0, sexp.named)
        rinterface.baseenv.get("identity")(sexp)
        self.assertEqual(2, sexp.named)
        sexp2 = sexp.__deepcopy__()
        self.assertEqual(sexp.typeof, sexp2.typeof)
        self.assertEqual(list(sexp), list(sexp2))
        self.assertFalse(sexp.rsame(sexp2))
        self.assertEqual(0, sexp2.named)
        # should be the same as above, but just in case:
        sexp3 = copy.deepcopy(sexp)
        self.assertEqual(sexp.typeof, sexp3.typeof)
        self.assertEqual(list(sexp), list(sexp3))
        self.assertFalse(sexp.rsame(sexp3))
        self.assertEqual(0, sexp3.named)

class RNULLTestCase(unittest.TestCase):
    def testRNULLType_nonzero(self):
        NULL = rinterface.RNULLType()
        self.assertFalse(NULL)


def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(SexpTestCase)
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(RNULLTestCase))
    return suite

if __name__ == '__main__':
    tr = unittest.TextTestRunner(verbosity = 2)
    tr.run(suite())
