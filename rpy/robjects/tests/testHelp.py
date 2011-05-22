import unittest
import rpy2.robjects as robjects
import rpy2.robjects.help as rh
rinterface = robjects.rinterface


class PackageTestCase(unittest.TestCase):

    def testInit(self):
        base_help = rh.Package('base')
        self.assertEqual('NULL', base_help.object2alias['NULL'])

    def testFetch(self):
        base_help = rh.Package('base')
        f = base_help.fetch('RdUtils')
        self.assertTrue('title' in f.sections.keys())

class PageTestCase(unittest.TestCase):
    
    def testInit(self):
        base_help = rh.Package('base')
        p = base_help.fetch('RdUtils')
        self.assertEqual('title', p.sections.keys()[0])
    
    def testToDocstring(self):
        base_help = rh.Package('base')
        p = base_help.fetch('RdUtils')
        ds = p.to_docstring()
        self.assertEqual('title', ds[0])
        self.assertEqual('-----', ds[2])

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(PackageTestCase)
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(PageTestCase))
    return suite

if __name__ == '__main__':
     unittest.main()
