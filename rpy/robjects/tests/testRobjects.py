import unittest
import rpy2.robjects as robjects
rinterface = robjects.rinterface
import array

class RvectorTestCase(unittest.TestCase):

    def testGetItem(self):
        letters_R = robjects.r["letters"]
        self.assertTrue(isinstance(letters_R, robjects.Rvector))
        letters = (('a', 0), ('b', 1), ('c', 2), ('x', 23), ('y', 24), ('z', 25))
        for l, i in letters:
            self.assertTrue(letters_R[i]._sexp[0] == l)
        
        as_list_R = robjects.r["as.list"]
        seq_R = robjects.r["seq"]
        
        mySeq = seq_R(0, 10)
        
        myList = as_list_R(mySeq)
        
        for i, li in enumerate(myList):
            self.assertEquals(i, myList[i][0]._sexp[0])

    def testOperators(self):
        seq_R = robjects.r["seq"]
        mySeq = seq_R(0, 10)
        mySeqAdd = mySeq + 2
        for i, li in enumerate(mySeq):
            self.assertEquals(i + 2, mySeqAdd[i]._sexp[0])

        mySeqAdd = mySeq + mySeq
        for i, li in enumerate(mySeq):
            self.assertEquals(mySeq[i]._sexp[0] * 2, mySeqAdd[i]._sexp[0])

        
    def testSubset(self):
        seq_R = robjects.r["seq"]
        mySeq = seq_R(0, 10)
        # R indexing starts at one
        myIndex = robjects.Rvector(array.array('i', range(1, 11, 2)))

        mySubset = mySeq.subset(myIndex)
        #import pdb; pdb.set_trace()
        for i, si in enumerate(myIndex):
            self.assertEquals(mySeq[si._sexp[0]-1]._sexp[0], mySubset[i]._sexp[0])

        # recycling rule
        v = robjects.Rvector(array.array('i', range(1, 23)))
        m = robjects.r.matrix(v, ncol = 2)
        col = m.subset(True, 1)
        #import pdb; pdb.set_trace()
        self.assertEquals(11, len(col))
        
        

    def testMapperR2Python(self):
        sexp = rinterface.globalEnv.get("letters")
        ob = robjects.defaultRobjects2PyMapper(sexp)
        self.assertTrue(isinstance(ob, 
                                   robjects.Rvector))

        sexp = rinterface.globalEnv.get("T")
        ob = robjects.defaultRobjects2PyMapper(sexp)
        self.assertTrue(isinstance(ob, 
                                   robjects.Rvector))

        sexp = rinterface.globalEnv.get("plot")
        ob = robjects.defaultRobjects2PyMapper(sexp)
        self.assertTrue(isinstance(ob, 
                                   robjects.Rfunction))

        sexp = rinterface.globalEnv.get(".GlobalEnv")
        self.assertTrue(isinstance(robjects.defaultRobjects2PyMapper(sexp), robjects.Renvironment))

        #FIXME: test S4

    def testMapperPy2R(self):
        py = 1
        rob = robjects.defaultPy2RobjectsMapper(py)
        self.assertTrue(isinstance(rob, robjects.Rvector))
        
        py = True
        rob = robjects.defaultPy2RobjectsMapper(py)
        self.assertTrue(isinstance(rob, robjects.Rvector))
        self.assertEquals(rinterface.LGLSXP, rob._sexp.typeof())

        #FIXME: more tests

if __name__ == '__main__':
     unittest.main()
