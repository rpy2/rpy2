import unittest
import rpy2.robjects as robjects
import rpy2.robjects.help as rh
rinterface = robjects.rinterface

class PackageTestCase(unittest.TestCase):

    def testInit(self):
        base_help = rh.Package('base')
        self.assertEquals('Sd2Rd', base_help.object2alias['RdUtils'])

    def testFetch(self):
        base_help = rh.Package('base')
        f = base_help.fetch('RdUtils')
        self.assertEquals('\\title', f[0].do_slot('Rd_tag')[0])

class PageTestCase(unittest.TestCase):
    
    def testInit(self):
        base_help = rh.Package('base')
        f = base_help.fetch('RdUtils')
        p = rh.Page(f)
        self.assertEquals('title', p.sections.keys()[0])
    
    def testToDocstring(self):
        base_help = rh.Package('base')
        f = base_help.fetch('RdUtils')
        p = rh.Page(f)
        ds = p.to_docstring()
        self.assertEquals('title', ds[0])
        self.assertEquals('-----', ds[2])

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(PackageTestCase)
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(PageTestCase))
    return suite

if __name__ == '__main__':
     unittest.main()
