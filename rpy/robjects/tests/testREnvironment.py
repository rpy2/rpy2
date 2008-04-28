import unittest
import rpy2.robjects as robjects
rinterface = robjects.rinterface
import array

class REnvironmentTestCase(unittest.TestCase):
    def testNew(self):
        env = robjects.Renvironment()
        self.assertEquals(rinterface.ENVSXP, env.getSexp().typeof())
        self.assertRaises(ValueError, robjects.Renvironment, 'a')

    def testSetItem(self):
        env = robjects.Renvironment()
        env['a'] = 123
        self.assertTrue('a' in env)

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(REnvironmentTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
