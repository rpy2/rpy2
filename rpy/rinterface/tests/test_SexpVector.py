import unittest
import rpy2.rinterface as rinterface

#FIXME: can starting and stopping an embedded R be done several times ?
rinterface.initEmbeddedR("foo", "--vanilla", "--no-save", "--quiet")

def floatEqual(x, y, epsilon = 0.00000001):
    return abs(x - y) < epsilon

class SexpVectorTestCase(unittest.TestCase):
    #def setUpt(self):
    #    rinterface.initEmbeddedR("foo", "--no-save")

    #def tearDown(self):
    #    rinterface.endEmbeddedR(1);

    def testNewBool(self):
        sexp = rinterface.SexpVector([True, ], rinterface.LGLSXP)
        isLogical = rinterface.globalEnv.get("is.logical")
        ok = isLogical(sexp)[0]
        self.assertTrue(ok)

        sexp = rinterface.SexpVector(["a", ], rinterface.LGLSXP)
        isNA = rinterface.globalEnv.get("is.na")
        ok = isNA(sexp)[0]
        self.assertTrue(ok)


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

        self.assertEquals(2, len(sexp))
        

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

    def testAssignItemDifferentType(self):
        c_R = rinterface.globalEnv.get("c")
        myVec = c_R(rinterface.SexpVector([0, 1, 2, 3, 4, 5], rinterface.INTSXP))
        self.assertRaises(ValueError, myVec.__setitem__, 0, rinterface.SexpVector(["a", ], rinterface.STRSXP))
        
    def testAssignItemOutOfBound(self):
        c_R = rinterface.globalEnv.get("c")
        myVec = c_R(rinterface.SexpVector([0, 1, 2, 3, 4, 5], rinterface.INTSXP))
        self.assertRaises(ValueError, myVec.__setitem__, 10, rinterface.SexpVector([1, ], rinterface.INTSXP))

    def testAssignItemInt(self):
        c_R = rinterface.globalEnv.get("c")
        myVec = c_R(rinterface.SexpVector([0, 1, 2, 3, 4, 5], rinterface.INTSXP))
        myVec[0] = rinterface.SexpVector([100, ], rinterface.INTSXP)
        self.assertTrue(myVec[0] == 100)

        myVec[3] = rinterface.SexpVector([100, ], rinterface.INTSXP)
        self.assertTrue(myVec[3] == 100)

    def testAssignItemReal(self):
        c_R = rinterface.globalEnv.get("c")
        myVec = c_R(rinterface.SexpVector([0.0, 1.0, 2.0, 3.0, 4.0, 5.0], rinterface.REALSXP))
        myVec[0] = rinterface.SexpVector([100.0, ], rinterface.REALSXP)
        self.assertTrue(floatEqual(myVec[0], 100.0))

        myVec[3] = rinterface.SexpVector([100.0, ], rinterface.REALSXP)
        self.assertTrue(floatEqual(myVec[3], 100.0))

    def testAssignItemLogical(self):
        c_R = rinterface.globalEnv.get("c")
        myVec = c_R(rinterface.SexpVector([True, False, True, True, False], rinterface.LGLSXP))
        myVec[0] = rinterface.SexpVector([False, ], rinterface.LGLSXP)
        self.assertFalse(myVec[0])

        myVec[3] = rinterface.SexpVector([False, ], rinterface.LGLSXP)
        self.assertFalse(myVec[3])

    def testAssignItemComplex(self):
        c_R = rinterface.globalEnv.get("c")
        myVec = c_R(rinterface.SexpVector([1.0+2.0j, 2.0+2.0j, 3.0+2.0j, 4.0+2.0j, 5.0+2.0j], rinterface.CPLXSXP))
        myVec[0] = rinterface.SexpVector([100.0+200.0j, ], rinterface.CPLXSXP)
        self.assertTrue(floatEqual(myVec[0].real, 100.0))
        self.assertTrue(floatEqual(myVec[0].imag, 200.0))

        myVec[3] = rinterface.SexpVector([100.0+200.0j, ], rinterface.CPLXSXP)
        self.assertTrue(floatEqual(myVec[3].real, 100.0))
        self.assertTrue(floatEqual(myVec[3].imag, 200.0))

    def testAssignItemList(self):
        myVec = rinterface.SexpVector([rinterface.SexpVector(["a", ], rinterface.STRSXP), 
                                       rinterface.SexpVector([1, ], rinterface.INTSXP),
                                       rinterface.SexpVector([3, ], rinterface.INTSXP)], rinterface.VECSXP)
        
        myVec[0] = rinterface.SexpVector([rinterface.SexpVector([100.0, ], rinterface.REALSXP), ], rinterface.VECSXP)
        self.assertTrue(floatEqual(myVec[0][0][0], 100.0))
        
        myVec[2] = rinterface.SexpVector([rinterface.SexpVector(["a", ], rinterface.STRSXP), ], rinterface.VECSXP) 
        self.assertTrue(myVec[2][0][0] == "a")
        
    def testAssignItemString(self):
        letters_R = rinterface.globalEnv.get("letters")
        #FIXME: segfaults
        #letters_R[0] = rinterface.SexpVector(["z", ], rinterface.STRSXP)
        self.assertTrue(letters_R[0] == "z")

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(SexpVectorTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
