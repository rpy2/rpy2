import unittest
import rpy2.robjects as robjects
rinterface = robjects.rinterface
import array

class RObjectTestCase(unittest.TestCase):

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
        self.assertEquals(rinterface.LGLSXP, rob.typeof())

        #FIXME: more tests

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(RObjectTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
