import unittest

from rpy2.robjects.packages import importr, data
datasets = importr('datasets')
mtcars = data(datasets).fetch('mtcars')['mtcars']
from rpy2.robjects import r

from rpy2.robjects.lib import grdevices

class GrdevicesTestCase(unittest.TestCase):

    def testSetup(self):
        pass

    def tearDown(self):
        pass

    def testContextManagerNoPlot(self):
        with grdevices.render_to_bytesio(grdevices.png) as b:
            pass
        self.assertEqual(0, len(b.getvalue()))

    def testContextManagerPlot(self):
        with grdevices.render_to_bytesio(grdevices.png) as b:
            r(''' plot(0) ''')
        self.assertTrue(len(b.getvalue()) > 0)
        
def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(GrdevicesTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
