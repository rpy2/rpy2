import unittest
import sys
import rpy2.rinterface as ri

try:
    #FIXME: can starting and stopping an embedded R be done several times ?
    ri.initEmbeddedR()
except:
    pass

def floatEqual(x, y, epsilon = 0.00000001):
    return abs(x - y) < epsilon

class SexpVectorTestCase(unittest.TestCase):
    #def setUpt(self):
    #    ri.initEmbeddedR("foo", "--no-save")

    #def tearDown(self):
    #    ri.endEmbeddedR(1);

    def testMissinfType(self):
        self.assertRaises(ValueError, ri.SexpVector, [2, ])

    def testNewBool(self):
        sexp = ri.SexpVector([True, ], ri.LGLSXP)
        isLogical = ri.globalEnv.get("is.logical")
        ok = isLogical(sexp)[0]
        self.assertTrue(ok)
        self.assertTrue(sexp[0])

        sexp = ri.SexpVector(["a", ], ri.LGLSXP)
        isLogical = ri.globalEnv.get("is.logical")
        ok = isLogical(sexp)[0]
        self.assertTrue(ok)
        self.assertTrue(sexp[0])

    def testNewInt(self):
        sexp = ri.SexpVector([1, ], ri.INTSXP)
        isInteger = ri.globalEnv.get("is.integer")
        ok = isInteger(sexp)[0]
        self.assertTrue(ok)

        sexp = ri.SexpVector(["a", ], ri.INTSXP)
        isNA = ri.globalEnv.get("is.na")
        ok = isNA(sexp)[0]
        self.assertTrue(ok)

    def testNewReal(self):
        sexp = ri.SexpVector([1.0, ], ri.REALSXP)
        isNumeric = ri.globalEnv.get("is.numeric")
        ok = isNumeric(sexp)[0]
        self.assertTrue(ok)

        sexp = ri.SexpVector(["a", ], ri.REALSXP)
        isNA = ri.globalEnv.get("is.na")
        ok = isNA(sexp)[0]
        self.assertTrue(ok)

    def testNewComplex(self):
        sexp = ri.SexpVector([1.0 + 1.0j, ], ri.CPLXSXP)
        isComplex = ri.globalEnv.get("is.complex")
        ok = isComplex(sexp)[0]
        self.assertTrue(ok)

    def testNewString(self):
        sexp = ri.SexpVector(["abc", ], ri.STRSXP)
        isCharacter = ri.globalEnv.get("is.character")
        ok = isCharacter(sexp)[0]
        self.assertTrue(ok)

        sexp = ri.SexpVector([1, ], ri.STRSXP)
        isCharacter = ri.globalEnv.get("is.character")
        ok = isCharacter(sexp)[0]
        self.assertTrue(ok)

        ri.NA_STRING[0]

    def testNewVector(self):
        sexp_char = ri.SexpVector(["abc", ], 
                                          ri.STRSXP)
        sexp_int = ri.SexpVector([1, ], 
                                         ri.INTSXP)
        sexp = ri.SexpVector([sexp_char, sexp_int], 
                                     ri.VECSXP)
        isList = ri.globalEnv.get("is.list")
        ok = isList(sexp)[0]
        self.assertTrue(ok)

        self.assertEquals(2, len(sexp))
        

    def testNew_InvalidType(self):
        self.assertRaises(ValueError, ri.SexpVector, [1, ], -1)
        self.assertRaises(ValueError, ri.SexpVector, [1, ], 250)

    def testGetItem(self):
        letters_R = ri.globalEnv.get("letters")
        self.assertTrue(isinstance(letters_R, ri.SexpVector))
        letters = (('a', 0), ('b', 1), ('c', 2), ('x', 23), ('y', 24), ('z', 25))
        for l, i in letters:
            self.assertTrue(letters_R[i] == l)
        
        Rlist = ri.globalEnv.get("list")
        seq_R = ri.globalEnv.get("seq")
        
        mySeq = seq_R(ri.SexpVector([0, ], ri.INTSXP),
                      ri.SexpVector([10, ], ri.INTSXP))
        
        myList = Rlist(s=mySeq, l=letters_R)
        idem = ri.globalEnv.get("identical")

        self.assertTrue(idem(mySeq, myList[0]))
        self.assertTrue(idem(letters_R, myList[1]))

    def testGetItemOutOfBound(self):
        myVec = ri.SexpVector([0, 1, 2, 3, 4, 5], ri.INTSXP)
        self.assertRaises(IndexError, myVec.__getitem__, 10)
        if (sys.maxint > ri.R_LEN_T_MAX):
            self.assertRaises(IndexError, myVec.__getitem__, 
                              ri.R_LEN_T_MAX+1)

    def testAssignItemDifferentType(self):
        c_R = ri.globalEnv.get("c")
        myVec = c_R(ri.SexpVector([0, 1, 2, 3, 4, 5], ri.INTSXP))
        #import pdb; pdb.set_trace()
        self.assertRaises(ValueError, myVec.__setitem__, 0, 
                          ri.SexpVector(["a", ], ri.STRSXP))
        
    def testAssignItemOutOfBound(self):
        c_R = ri.globalEnv.get("c")
        myVec = c_R(ri.SexpVector([0, 1, 2, 3, 4, 5], ri.INTSXP))
        self.assertRaises(IndexError, myVec.__setitem__, 10, 
                          ri.SexpVector([1, ], ri.INTSXP))

    def testAssignItemInt(self):
        c_R = ri.globalEnv.get("c")
        myVec = c_R(ri.SexpVector([0, 1, 2, 3, 4, 5], ri.INTSXP))
        myVec[0] = ri.SexpVector([100, ], ri.INTSXP)
        self.assertTrue(myVec[0] == 100)

        myVec[3] = ri.SexpVector([100, ], ri.INTSXP)
        self.assertTrue(myVec[3] == 100)

    def testAssignItemReal(self):
        c_R = ri.globalEnv.get("c")
        myVec = c_R(ri.SexpVector([0.0, 1.0, 2.0, 3.0, 4.0, 5.0], 
                                          ri.REALSXP))
        myVec[0] = ri.SexpVector([100.0, ], ri.REALSXP)
        self.assertTrue(floatEqual(myVec[0], 100.0))

        myVec[3] = ri.SexpVector([100.0, ], ri.REALSXP)
        self.assertTrue(floatEqual(myVec[3], 100.0))

    def testAssignItemLogical(self):
        c_R = ri.globalEnv.get("c")
        myVec = c_R(ri.SexpVector([True, False, True, True, False], 
                                          ri.LGLSXP))
        myVec[0] = ri.SexpVector([False, ], ri.LGLSXP)
        self.assertFalse(myVec[0])

        myVec[3] = ri.SexpVector([False, ], ri.LGLSXP)
        self.assertFalse(myVec[3])

    def testAssignItemComplex(self):
        c_R = ri.globalEnv.get("c")
        myVec = c_R(ri.SexpVector([1.0+2.0j, 2.0+2.0j, 3.0+2.0j, 4.0+2.0j, 5.0+2.0j], 
                                          ri.CPLXSXP))
        myVec[0] = ri.SexpVector([100.0+200.0j, ], ri.CPLXSXP)
        self.assertTrue(floatEqual(myVec[0].real, 100.0))
        self.assertTrue(floatEqual(myVec[0].imag, 200.0))

        myVec[3] = ri.SexpVector([100.0+200.0j, ], ri.CPLXSXP)
        self.assertTrue(floatEqual(myVec[3].real, 100.0))
        self.assertTrue(floatEqual(myVec[3].imag, 200.0))

    def testAssignItemList(self):
        myVec = ri.SexpVector([ri.SexpVector(["a", ], ri.STRSXP), 
                                       ri.SexpVector([1, ], ri.INTSXP),
                                       ri.SexpVector([3, ], ri.INTSXP)], 
                                      ri.VECSXP)
        
        myVec[0] = ri.SexpVector([ri.SexpVector([100.0, ], 
ri.REALSXP), ], 
                                         ri.VECSXP)
        self.assertTrue(floatEqual(myVec[0][0][0], 100.0))
        
        myVec[2] = ri.SexpVector([ri.SexpVector(["a", ], ri.STRSXP), ], 
                                         ri.VECSXP) 
        self.assertTrue(myVec[2][0][0] == "a")
        
    def testAssignItemString(self):
        letters_R = ri.SexpVector("abcdefghij", ri.STRSXP)
        self.assertRaises(ValueError, letters_R.__setitem__, 0, ri.SexpVector([1, ], 
                                                                                      ri.INTSXP))

        letters_R[0] = ri.SexpVector(["z", ], ri.STRSXP)
        self.assertTrue(letters_R[0] == "z")

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(SexpVectorTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
