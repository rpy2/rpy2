import unittest
import rpy2.robjects as robjects
ri = robjects.rinterface
import array
import rpy2.rlike.container as rlc

rlist = robjects.baseenv["list"]

class VectorTestCase(unittest.TestCase):

    def testNew(self):
        identical = ri.baseenv["identical"]
        py_a = array.array('i', [1,2,3])
        ro_v = robjects.Vector(py_a)
        self.assertEquals(ro_v.typeof, ri.INTSXP)
        
        ri_v = ri.SexpVector(py_a, ri.INTSXP)
        ro_v = robjects.Vector(ri_v)

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

    def testNewFactorVector(self):
        vec = robjects.FactorVector(robjects.StrVector('abaabc'))
        self.assertEquals(6, len(vec))

    def testFactorVector_isordered(self):
        vec = robjects.FactorVector(robjects.StrVector('abaabc'))
        self.assertFalse(vec.isordered)

    def testFactorVector_nlevels(self):
        vec = robjects.FactorVector(robjects.StrVector('abaabc'))
        self.assertEquals(3, vec.nlevels)

    def testFactorVector_levels(self):
        vec = robjects.FactorVector(robjects.StrVector('abaabc'))
        self.assertEquals(3, len(vec.levels))
        self.assertEquals(set(('a','b','c')), set(tuple(vec.levels)))


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
        mySeqAdd = mySeq.ro + 2
        for i, li in enumerate(mySeq):
            self.assertEquals(li + 2, mySeqAdd[i])

    def testRMultOperators(self):
        seq_R = robjects.r["seq"]
        mySeq = seq_R(0, 10)
        mySeqAdd = mySeq.ro + mySeq
        for i, li in enumerate(mySeq):
            self.assertEquals(li * 2, mySeqAdd[i])

    def testRPowerOperator(self):
        seq_R = robjects.r["seq"]
        mySeq = seq_R(0, 10)
        mySeqPow = mySeq.ro ** 2
        for i, li in enumerate(mySeq):
            self.assertEquals(li ** 2, mySeqPow[i])

 
    def testGetItem(self):
        letters = robjects.baseenv["letters"]
        self.assertEquals('a', letters[0])
        self.assertEquals('z', letters[25])

    def testGetItemOutOfBounds(self):
        letters = robjects.baseenv["letters"]
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
        idem = robjects.baseenv["identical"]
        self.assertTrue(idem(letters, mylist[0]))
        self.assertTrue(idem("foo", mylist[1]))

    def testGetNames(self):
        vec = robjects.Vector(array.array('i', [1,2,3]))
        v_names = [robjects.baseenv["letters"][x] for x in (0,1,2)]
        #FIXME: simplify this
        r_names = robjects.baseenv["c"](*v_names)
        vec = robjects.baseenv["names<-"](vec, r_names)
        for i in xrange(len(vec)):
            self.assertEquals(v_names[i], vec.names[i])

        vec.names[0] = 'x'

    def testSetNames(self):
        vec = robjects.Vector(array.array('i', [1,2,3]))
        names = ['x', 'y', 'z']
        vec.names = names
        for i in xrange(len(vec)):
            self.assertEquals(names[i], vec.names[i])

    def testNAinteger(self):
        vec = robjects.IntVector(range(3))
        vec[0] = robjects.NA_integer
        self.assertTrue(robjects.baseenv['is.na'](vec)[0])
    def testNAreal(self):
        vec = robjects.FloatVector((1.0, 2.0, 3.0))
        vec[0] = robjects.NA_real
        self.assertTrue(robjects.baseenv['is.na'](vec)[0])
    def testNAbool(self):
        vec = robjects.BoolVector((True, False, True))
        vec[0] = robjects.NA_bool
        self.assertTrue(robjects.baseenv['is.na'](vec)[0])
    def testNAcomplex(self):
        vec = robjects.ComplexVector((1+1j, 2+2j, 3+3j))
        vec[0] = robjects.NA_complex
        self.assertTrue(robjects.baseenv['is.na'](vec)[0])
    def testNAcharacter(self):
        vec = robjects.StrVector('abc')
        vec[0] = robjects.NA_character
        self.assertTrue(robjects.baseenv['is.na'](vec)[0])

    def testIteritems(self):
        vec = robjects.IntVector(range(3))
        vec.names = robjects.StrVector('abc')
        names = [k for k,v in vec.iteritems()]
        self.assertEquals(['a', 'b', 'c'], names)
        values = [v for k,v in vec.iteritems()]
        self.assertEquals([0, 1, 2], values)

    def testIteritemsNoNames(self):
        vec = robjects.IntVector(range(3))
        names = [k for k,v in vec.iteritems()]
        self.assertEquals([None, None, None], names)
        values = [v for k,v in vec.iteritems()]
        self.assertEquals([0, 1, 2], values)


class ExtractDelegatorTestCase(unittest.TestCase):

    def setUp(self):
        self.console = robjects.rinterface.get_writeconsole()

    def tearDown(self):
        robjects.rinterface.set_writeconsole(self.console)

    def testExtractByIndex(self):
        seq_R = robjects.baseenv["seq"]
        mySeq = seq_R(0, 10)
        # R indexing starts at one
        myIndex = robjects.Vector(array.array('i', range(1, 11, 2)))

        mySubset = mySeq.rx(myIndex)
        for i, si in enumerate(myIndex):
            self.assertEquals(mySeq[si-1], mySubset[i])
        
    def testExtractByName(self):
        seq_R = robjects.baseenv["seq"]
        mySeq = seq_R(0, 25)

        letters = robjects.baseenv["letters"]
        mySeq = robjects.baseenv["names<-"](mySeq, 
                                                     letters)

        # R indexing starts at one
        myIndex = robjects.Vector(letters[2])

        mySubset = mySeq.rx(myIndex)

        for i, si in enumerate(myIndex):
            self.assertEquals(2, mySubset[i])

    def testExtractIndexError(self):
        seq_R = robjects.baseenv["seq"]
        mySeq = seq_R(0, 10)
        # R indexing starts at one
        myIndex = robjects.Vector(['a', 'b', 'c'])

        def noconsole(x):
            pass
        robjects.rinterface.set_writeconsole(noconsole)

        self.assertRaises(ri.RRuntimeError, mySeq.rx, myIndex)


       
    def testReplace(self):
        vec = robjects.r.seq(1, 10)
        i = array.array('i', [1, 3])
        vec.rx[rlc.TaggedList((i, ))] = 20
        self.assertEquals(20, vec[0])
        self.assertEquals(2, vec[1])
        self.assertEquals(20, vec[2])
        self.assertEquals(4, vec[3])

        i = array.array('i', [1, 5])
        vec.rx[rlc.TaggedList((i, ))] = 50
        self.assertEquals(50, vec[0])
        self.assertEquals(2, vec[1])
        self.assertEquals(20, vec[2])
        self.assertEquals(4, vec[3])
        self.assertEquals(50, vec[4])
                         
    def testExtractRecyclingRule(self):
        # recycling rule
        v = robjects.Vector(array.array('i', range(1, 23)))
        m = robjects.r.matrix(v, ncol = 2)
        col = m.rx(True, 1)
        self.assertEquals(11, len(col))

    def testExtractList(self):
        # list
        letters = robjects.baseenv["letters"]
        myList = rlist(l=letters, f="foo")
        idem = robjects.baseenv["identical"]
        self.assertTrue(idem(letters, myList.rx("l")[0]))
        self.assertTrue(idem("foo", myList.rx("f")[0]))


def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(VectorTestCase)
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(ExtractDelegatorTestCase))
    return suite

if __name__ == '__main__':
     unittest.main()
