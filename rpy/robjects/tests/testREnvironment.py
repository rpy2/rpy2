import unittest
import rpy2.robjects as robjects
rinterface = robjects.rinterface
import array

class REnvironmentTestCase(unittest.TestCase):
    def testNew(self):
        env = robjects.REnvironment()
        self.assertEquals(rinterface.ENVSXP, env.typeof)

    def testNewValueError(self):
        self.assertRaises(ValueError, robjects.REnvironment, 'a')

    def testSetItem(self):
        env = robjects.REnvironment()
        env['a'] = 123
        self.assertTrue('a' in env)

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(REnvironmentTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
