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
        self.assertTrue(isinstance(pck.a, robjects.Vector))
        self.assertTrue(isinstance(pck.b, robjects.Vector))
        self.assertTrue(isinstance(pck.c, robjects.Function))


    def testNewWithDot(self):
        env = robjects.Environment()
        env['a.a'] = robjects.StrVector('abcd')
        env['b'] = robjects.IntVector((1,2,3))
        env['c'] = robjects.r(''' function(x) x^2''')
        pck = robjects.packages.Package(env, "dummy_package")
        self.assertTrue(isinstance(pck.a_a, robjects.Vector))
        self.assertTrue(isinstance(pck.b, robjects.Vector))
        self.assertTrue(isinstance(pck.c, robjects.Function))

    def testNewWithDotConflict(self):
        env = robjects.Environment()
        env['a.a'] = robjects.StrVector('abcd')
        env['a_a'] = robjects.IntVector((1,2,3))
        env['c'] = robjects.r(''' function(x) x^2''')
        self.assertRaises(packages.LibraryError,
                          robjects.packages.Package,
                          env, "dummy_package")


    def testNewWithDotConflict(self):
        env = robjects.Environment()
        env['__dict__'] = robjects.StrVector('abcd')
        env['a_a'] = robjects.IntVector((1,2,3))
        env['c'] = robjects.r(''' function(x) x^2''')
        self.assertRaises(packages.LibraryError,
                          robjects.packages.Package,
                          env, "dummy_package")

class SignatureTranslatedAnonymousPackagesTestCase(unittest.TestCase):
    def testNew(self):
        string = """
   square <- function(x) {
       return(x^2)
   }

   cube <- function(x) {
       return(x^3)
   }
   """
        powerpack = packages.SignatureTranslatedAnonymousPackage(string, "powerpack")
        self.assertTrue(hasattr(powerpack, 'square'))
        self.assertTrue(hasattr(powerpack, 'cube'))


class ImportrTestCase(unittest.TestCase):
    def testImportStats(self):
        stats = robjects.packages.importr('stats')
        self.assertTrue(isinstance(stats, robjects.packages.Package))
        
    def testImportDatasets(self):
        datasets = robjects.packages.importr('datasets')
        self.assertTrue(isinstance(datasets, robjects.packages.Package))
        self.assertTrue(isinstance(datasets.data, 
                                   robjects.packages.PackageData))
        
class WherefromTestCase(unittest.TestCase):
    def testWherefrom(self):
        stats = robjects.packages.importr('stats')
        rnorm_pack = robjects.packages.wherefrom('rnorm')
        self.assertEqual('package:stats',
                          rnorm_pack.do_slot('name')[0])
        
def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(PackagesTestCase)
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(ImportrTestCase))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(WherefromTestCase))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(SignatureTranslatedAnonymousPackagesTestCase))
    return suite

if __name__ == '__main__':
     unittest.main()
