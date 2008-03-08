import unittest
import rpy.rinterface as rinterface

#FIXME: can starting and stopping an embedded R be done several times ?
rinterface.initEmbeddedR("foo", "--vanilla", "--no-save", "--quiet")

class SexpVectorTestCase(unittest.TestCase):
    #def setUpt(self):
    #    rinterface.initEmbeddedR("foo", "--no-save")

    #def tearDown(self):
    #    rinterface.endEmbeddedR(1);

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
