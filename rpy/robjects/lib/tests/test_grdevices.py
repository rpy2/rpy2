import unittest
import os
import tempfile

from rpy2.robjects.packages import importr, data
datasets = importr('datasets')
mtcars = data(datasets).fetch('mtcars')['mtcars']
from rpy2.robjects import r

from rpy2.robjects.lib import grdevices

class GrdevicesTestCase(unittest.TestCase):

    _todelete = list()
    
    def testSetup(self):
        pass

    def tearDown(self):
        for fn in self._todelete:
            if os.path.exists(fn):
                os.unlink(fn)

    def testRenderToBytesNoPlot(self):
        with grdevices.render_to_bytesio(grdevices.png) as b:
            pass
        self.assertEqual(0, len(b.getvalue()))

    def testRenderToFile(self):
        fn = tempfile.mktemp(suffix=".png")
        with grdevices.render_to_file(grdevices.png,
                                      filename=fn) as d:
            r(''' plot(0) ''')
        self._todelete.append(fn)
        self.assertTrue(os.path.exists(fn))

    def testRenderToBytesPlot(self):
        with grdevices.render_to_bytesio(grdevices.png) as b:
            r(''' plot(0) ''')
        self.assertTrue(len(b.getvalue()) > 0)
        
def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(GrdevicesTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
