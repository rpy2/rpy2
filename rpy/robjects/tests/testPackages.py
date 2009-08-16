import unittest
import rpy2.robjects as robjects
import rpy2.robjects.packages as packages
rinterface = robjects.rinterface

class PackagesTestCase(unittest.TestCase):

    def testNew(self):
        env = robjects.Environment()
        env['a'] = robjects.StrVector('abcd')
        env['b'] = robjects.IntVector((1,2,3))
        env['c'] = robjects.r(''' function(x) x^2''')
        pck = robjects.packages.Package(env, "dummy_package")
        self.assertTrue(isinstance(pck.a, robjects.RVector))
        self.assertTrue(isinstance(pck.b, robjects.RVector))
        self.assertTrue(isinstance(pck.b, robjects.Function))


    def testNewWithDot(self):
        env = robjects.Environment()
        env['a.a'] = robjects.StrVector('abcd')
        env['b'] = robjects.IntVector((1,2,3))
        env['c'] = robjects.r(''' function(x) x^2''')
        pck = robjects.packages.Package(env, "dummy_package")
        self.assertTrue(isinstance(pck.a_a, robjects.RVector))
        self.assertTrue(isinstance(pck.b, robjects.RVector))
        self.assertTrue(isinstance(pck.c, robjects.Function))

    def testNewWithDotConflict(self):
        env = robjects.Environment()
        env['a.a'] = robjects.StrVector('abcd')
        env['a_a'] = robjects.IntVector((1,2,3))
        env['c'] = robjects.r(''' function(x) x^2''')
        self.assertRaises(packages.LibraryError,
                          robjects.packages.Package,
                          env, "dummy_package")
        

class ImportrTestCase(unittest.TestCase):
    def testImportStats(self):
        stats = robjects.packages.importr('stats', where = None)
        self.assertTrue(isinstance(stats, robjects.packages.Package))
        
def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(PackagesTestCase)
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(ImportrTestCase))
    return suite

if __name__ == '__main__':
     unittest.main()
