import unittest
import rpy.rinterface as rinterface

#FIXME: can starting and stopping an embedded R be done several times ?
rinterface.initEmbeddedR("foo", "--vanilla", "--no-save", "--quiet")

class SexpVectorTestCase(unittest.TestCase):
    #def setUpt(self):
    #    rinterface.initEmbeddedR("foo", "--no-save")

    #def tearDown(self):
    #    rinterface.endEmbeddedR(1);

    def testNewInt(self):
        sexp = rinterface.SexpVector([1, ], rinterface.INTSXP)
        isInteger = rinterface.globalEnv.get("is.integer")
        ok = isInteger(sexp)[0]
        self.assertTrue(ok)

        sexp = rinterface.SexpVector(["a", ], rinterface.INTSXP)
        isNA = rinterface.globalEnv.get("is.na")
        ok = isNA(sexp)[0]
        self.assertTrue(ok)

    def testNewReal(self):
        sexp = rinterface.SexpVector([1.0, ], rinterface.REALSXP)
        isNumeric = rinterface.globalEnv.get("is.numeric")
        ok = isNumeric(sexp)[0]
        self.assertTrue(ok)

        sexp = rinterface.SexpVector(["a", ], rinterface.REALSXP)
        isNA = rinterface.globalEnv.get("is.na")
        ok = isNA(sexp)[0]
        self.assertTrue(ok)

    def testNewComplex(self):
        sexp = rinterface.SexpVector([1.0 + 1.0j, ], rinterface.CPLXSXP)
        isComplex = rinterface.globalEnv.get("is.complex")
        ok = isComplex(sexp)[0]
        self.assertTrue(ok)

    def testNewString(self):
        sexp = rinterface.SexpVector(["abc", ], rinterface.STRSXP)
        isCharacter = rinterface.globalEnv.get("is.character")
        ok = isCharacter(sexp)[0]
        self.assertTrue(ok)

        #FIXME: elucidate what is happening here
        sexp = rinterface.SexpVector([1, ], rinterface.STRSXP)
        isNA = rinterface.globalEnv.get("is.na")
        ok = isNA(sexp)[0]
        self.assertTrue(ok)

    def testNewVector(self):
        sexp_char = rinterface.SexpVector(["abc", ], rinterface.STRSXP)
        sexp_int = rinterface.SexpVector([1, ], rinterface.INTSXP)
        sexp = rinterface.SexpVector([sexp_char, sexp_int], rinterface.VECSXP)
        isList = rinterface.globalEnv.get("is.list")
        ok = isList(sexp)[0]
        self.assertTrue(ok)

        

    def testNew_InvalidType(self):
        self.assertTrue(False)
        #FIXME
        self.assertRaises(ValueError, rinterface.SexpVector, [1, ], -1)

    def testGetItem(self):
        letters_R = rinterface.globalEnv.get("letters")
        self.assertTrue(isinstance(letters_R, rinterface.SexpVector))
        letters = (('a', 0), ('b', 1), ('c', 2), ('x', 23), ('y', 24), ('z', 25))
        for l, i in letters:
            self.assertTrue(letters_R[i] == l)
        
        as_list_R = rinterface.globalEnv.get("as.list")
        seq_R = rinterface.globalEnv.get("seq")
        
        mySeq = seq_R(rinterface.SexpVector([0, ], rinterface.INTSXP),
                      rinterface.SexpVector([10, ], rinterface.INTSXP))
        
        myList = as_list_R(mySeq)
        
        for i, li in enumerate(myList):
            self.assertEquals(i, myList[i][0])

if __name__ == '__main__':
     unittest.main()
