import unittest
import rpy.robjects as robjects
rinterface = robjects.rinterface
import array

class RvectorTestCase(unittest.TestCase):

    def testGetItem(self):
        letters_R = robjects.r["letters"]
        self.assertTrue(isinstance(letters_R, robjects.Rvector))
        letters = (('a', 0), ('b', 1), ('c', 2), ('x', 23), ('y', 24), ('z', 25))
        for l, i in letters:
            self.assertTrue(letters_R[i] == l)
        
        as_list_R = robjects.r["as.list"]
        seq_R = robjects.r["seq"]
        
        mySeq = seq_R(0, 10)
        
        myList = as_list_R(mySeq)
        
        for i, li in enumerate(myList):
            self.assertEquals(i, myList[i][0])

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
        seq_R = robjects.r["seq"]
        mySeq = seq_R(0, 10)
        # R indexing starts at one
        myIndex = robjects.Rvector(array.array('i', range(1, 11, 2)))

        mySubset = mySeq.subset(myIndex)
        for i, si in enumerate(myIndex):
            self.assertEquals(mySeq[si-1], mySubset[i])

    def testMapperR2Python(self):
        sexp = rinterface.globalEnv.get("letters")
        self.assertTrue(isinstance(robjects.defaultRobjects2PyMapper(sexp), robjects.Rvector))
        
        sexp = rinterface.globalEnv.get("plot")
        self.assertTrue(isinstance(robjects.defaultRobjects2PyMapper(sexp), robjects.Rfunction))

        sexp = rinterface.globalEnv.get(".GlobalEnv")
        self.assertTrue(isinstance(robjects.defaultRobjects2PyMapper(sexp), robjects.Renvironment))

        #FIXME: test S4

    def testMapperPy2R(self):
        py = 1
        self.assertTrue(isinstance(robjects.defaultPy2RobjectsMapper(py), robjects.Rvector))
        
        #FIXME: more tests

if __name__ == '__main__':
     unittest.main()
