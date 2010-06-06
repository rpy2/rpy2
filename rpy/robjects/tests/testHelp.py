import unittest
import rpy2.robjects as robjects
import rpy2.robjects.help as rh
rinterface = robjects.rinterface

class HelpTestCase(unittest.TestCase):

    def testPackage(self):
        base_help = rh.Package('base')
        self.assertEquals('Sd2Rd', base_help.object2alias['RdUtils'])

    def testPackageFetch(self):
        base_help = rh.Package('base')
        f = base_help.fetch('RdUtils')
        self.assertEquals('\\title', f[0].do_slot('Rd_tag')[0])

    def testPage(self):
        base_help = rh.Package('base')
        f = base_help.fetch('RdUtils')
        p = rh.Page(f)
        self.assertEquals('title', p.sections.keys()[0])
    
def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(HelpTestCase)
    #suite.addTest(unittest.TestLoader().loadTestsFromTestCase(ImportrTestCase))
    return suite

if __name__ == '__main__':
     unittest.main()
