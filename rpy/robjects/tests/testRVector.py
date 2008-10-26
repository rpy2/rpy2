import unittest
import rpy2.robjects as robjects
ri = robjects.rinterface
import array
import rpy2.rlike.container as rlc

rlist = robjects.baseNameSpaceEnv["list"]

class RVectorTestCase(unittest.TestCase):

    def testNew(self):
        identical = ri.baseNameSpaceEnv["identical"]
        py_a = array.array('i', [1,2,3])
        ro_v = robjects.RVector(py_a)
        self.assertEquals(ro_v.typeof, ri.INTSXP)
        
        ri_v = ri.SexpVector(py_a, ri.INTSXP)
        ro_v = robjects.RVector(ri_v)

        self.assertTrue(identical(ro_v, ri_v)[0])

        del(ri_v)
        self.assertEquals(ri.INTSXP, ro_v.typeof)

    def testNewStrVector(self):
        vec = robjects.StrVector(['abc', 'def'])
        self.assertEquals('abc', vec[0])
        self.assertEquals('def', vec[1])
        self.assertEquals(2, len(vec))

    def testNewIntVector(self):
        vec = robjects.IntVector([123, 456])
        self.assertEquals(123, vec[0])
        self.assertEquals(456, vec[1])
        self.assertEquals(2, len(vec))

    def testNewFloatVector(self):
        vec = robjects.FloatVector([123.0, 456.0])
        self.assertEquals(123.0, vec[0])
        self.assertEquals(456.0, vec[1])
        self.assertEquals(2, len(vec))

    def testNewBoolVector(self):
        vec = robjects.BoolVector([True, False])
        self.assertEquals(True, vec[0])
        self.assertEquals(False, vec[1])
        self.assertEquals(2, len(vec))

    def testAddOperators(self):
        seq_R = robjects.r["seq"]
        mySeqA = seq_R(0, 3)
        mySeqB = seq_R(5, 7)
        mySeqAdd = mySeqA + mySeqB

        self.assertEquals(len(mySeqA)+len(mySeqB), len(mySeqAdd))

        for i, li in enumerate(mySeqA):
            self.assertEquals(li, mySeqAdd[i])       
        for j, li in enumerate(mySeqB):
            self.assertEquals(li, mySeqAdd[i+j+1])

    def testRAddOperators(self):
        seq_R = robjects.r["seq"]
        mySeq = seq_R(0, 10)
        mySeqAdd = mySeq.r + 2
        for i, li in enumerate(mySeq):
            self.assertEquals(li + 2, mySeqAdd[i])

    def testRMultOperators(self):
        seq_R = robjects.r["seq"]
        mySeq = seq_R(0, 10)
        mySeqAdd = mySeq.r + mySeq
        for i, li in enumerate(mySeq):
            self.assertEquals(li * 2, mySeqAdd[i])

    def testRPowerOperator(self):
        seq_R = robjects.r["seq"]
        mySeq = seq_R(0, 10)
        mySeqPow = mySeq.r ** 2
        for i, li in enumerate(mySeq):
            self.assertEquals(li ** 2, mySeqPow[i])

        
    def testSubsetByIndex(self):
        seq_R = robjects.baseNameSpaceEnv["seq"]
        mySeq = seq_R(0, 10)
        # R indexing starts at one
        myIndex = robjects.RVector(array.array('i', range(1, 11, 2)))

        mySubset = mySeq.subset(myIndex)
        for i, si in enumerate(myIndex):
            self.assertEquals(mySeq[si-1], mySubset[i])

        # same with the delegator
        mySubset = mySeq.r[myIndex]
        for i, si in enumerate(myIndex):
            self.assertEquals(mySeq[si-1], mySubset[i])
        
    def testSubsetByName(self):
        seq_R = robjects.baseNameSpaceEnv["seq"]
        mySeq = seq_R(0, 25)

        letters = robjects.baseNameSpaceEnv["letters"]
        mySeq = robjects.baseNameSpaceEnv["names<-"](mySeq, 
                                                     letters)

        # R indexing starts at one
        myIndex = robjects.RVector(letters[2])

        mySubset = mySeq.subset(myIndex)

        for i, si in enumerate(myIndex):
            self.assertEquals(2, mySubset[i])

    def testSubsetIndexError(self):
        seq_R = robjects.baseNameSpaceEnv["seq"]
        mySeq = seq_R(0, 10)
        # R indexing starts at one
        myIndex = robjects.RVector(['a', 'b', 'c'])

        self.assertRaises(ri.RRuntimeError, mySeq.subset, myIndex)


    def testAssign(self):
        vec = robjects.r.seq(1, 10)
        i = array.array('i', [1, 3])
        vec = vec.assign(i, 20)
        self.assertEquals(20, vec[0])
        self.assertEquals(2, vec[1])
        self.assertEquals(20, vec[2])
        self.assertEquals(4, vec[3])

        i = array.array('i', [1, 5])
        vec = vec.assign(rlc.TaggedList([i, ]), 50)
        self.assertEquals(50, vec[0])
        self.assertEquals(2, vec[1])
        self.assertEquals(20, vec[2])
        self.assertEquals(4, vec[3])
        self.assertEquals(50, vec[4])
                         
    def testSubsetRecyclingRule(self):
        # recycling rule
        v = robjects.RVector(array.array('i', range(1, 23)))
        m = robjects.r.matrix(v, ncol = 2)
        col = m.subset(True, 1)
        self.assertEquals(11, len(col))

    def testSubsetList(self):
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

    def testGetItemOutOfBounds(self):
        letters = robjects.baseNameSpaceEnv["letters"]
        self.assertRaises(IndexError, letters.__getitem__, 26)

    def testSetItem(self):
        vec = robjects.r.seq(1, 10)
        vec[0] = 20
        self.assertEquals(20, vec[0])

    def testSetItemOutOfBounds(self):
        vec = robjects.r.seq(1, 10)
        self.assertRaises(IndexError, vec.__setitem__, 20, 20)

    def getItemList(self):
        mylist = rlist(letters, "foo")
        idem = robjects.baseNameSpaceEnv["identical"]
        self.assertTrue(idem(letters, mylist[0]))
        self.assertTrue(idem("foo", mylist[1]))

    def testGetNames(self):
        vec = robjects.RVector(array.array('i', [1,2,3]))
        v_names = [robjects.baseNameSpaceEnv["letters"][x] for x in (0,1,2)]
        #FIXME: simplify this
        r_names = robjects.baseNameSpaceEnv["c"](*v_names)
        vec = robjects.baseNameSpaceEnv["names<-"](vec, r_names)
        for i in xrange(len(vec)):
            self.assertEquals(v_names[i], vec.getnames()[i])

        vec.getnames()[0] = 'x'

    def testSetNames(self):
        vec = robjects.RVector(array.array('i', [1,2,3]))
        names = ['x', 'y', 'z']
        #FIXME: simplify this
        vec = vec.setnames(names)
        for i in xrange(len(vec)):
            self.assertEquals(names[i], vec.getnames()[i])

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(RVectorTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
