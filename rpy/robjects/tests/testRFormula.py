import unittest
import rpy2.robjects as robjects
rinterface = robjects.rinterface

class RFormulaTestCase(unittest.TestCase):

    def testNew(self):
        fml = robjects.RFormula("y ~ x")
        self.assertEquals("formula", fml.rclass[0])
        
    def testGetenvironment(self):
        fml = robjects.RFormula("y ~ x")
        env = fml.getenvironment()
        self.assertEquals("environment", env.rclass[0])

    def testSetenvironment(self):
        fml = robjects.RFormula("y ~ x")
        newenv = robjects.baseNameSpaceEnv['new.env']()
        env = fml.getenvironment()
        self.assertFalse(newenv.rsame(env))
        fml.setenvironment(newenv)
        env = fml.getenvironment()
        self.assertTrue(newenv.rsame(env))

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(RFormulaTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
