import unittest
import rpy2.robjects as robjects
rinterface = robjects.rinterface
import array

rlist = robjects.baseNameSpaceEnv["list"]

class RvectorTestCase(unittest.TestCase):
    def testNew(self):
        identical = rinterface.baseNameSpaceEnv["identical"]
        py_a = array.array('i', [1,2,3])
        ro_v = robjects.Rvector(py_a)
        self.assertEquals(ro_v.typeof(), rinterface.INTSXP)
        
        ri_v = rinterface.SexpVector(py_a, rinterface.INTSXP)
        ro_v = robjects.Rvector(ri_v)

        self.assertTrue(identical(ro_v._sexp, ri_v)[0])

        #FIXME: why isn't this working ?
        #del(ri_v)
        self.assertEquals(rinterface.INTSXP, ro_v.typeof())
        
    def testOperators(self):
        seq_R = robjects.r["seq"]
        mySeq = seq_R(0, 10)
        mySeqAdd = mySeq + 2
        for i, li in enumerate(mySeq):
            self.assertEquals(i + 2, mySeqAdd[i])

        mySeqAdd = mySeq + mySeq
        for i, li in enumerate(mySeq):
            self.assertEquals(mySeq[i] * 2, mySeqAdd[i])

        
    def testSubset(self):
        seq_R = robjects.baseNameSpaceEnv["seq"]
        mySeq = seq_R(0, 10)
        # R indexing starts at one
        myIndex = robjects.Rvector(array.array('i', range(1, 11, 2)))

        mySubset = mySeq.subset(myIndex)
        for i, si in enumerate(myIndex):
            self.assertEquals(mySeq[si-1], mySubset[i])

        # recycling rule
        v = robjects.Rvector(array.array('i', range(1, 23)))
        m = robjects.r.matrix(v, ncol = 2)
        col = m.subset(True, 1)
        self.assertEquals(11, len(col))

        # list
        letters = robjects.baseNameSpaceEnv["letters"]
        myList = rlist(l=letters, f="foo")
        idem = robjects.baseNameSpaceEnv["identical"]
        self.assertTrue(idem(letters, myList.subset("l")[0]))
        self.assertTrue(idem("foo", myList.subset("f")[0]))

    def testGetItem(self):
        letters = robjects.baseNameSpaceEnv["letters"]
        self.assertEquals('a', letters[0])
        self.assertEquals('z', letters[25])
        self.assertRaises(IndexError, letters.__getitem__, 26)
        
        mylist = rlist(letters, "foo")
        idem = robjects.baseNameSpaceEnv["identical"]
        self.assertTrue(idem(letters, mylist[0]))
        self.assertTrue(idem("foo", mylist[1]))

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(RvectorTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
