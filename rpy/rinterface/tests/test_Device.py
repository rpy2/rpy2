import unittest
import rpy2.rinterface as rinterface
import rpy2.rinterface.rpy_device as rdevice
import sys, os, subprocess, time, tempfile, signal
import tempfile

rinterface.initr()

class AbstractDeviceTestCase(unittest.TestCase):
    def setUp(self):
        self.gd = rdevice.GraphicalDevice()

    def tearDown(self):
        self.gd = None

    def _testGetSetBooleanAttr(self, name):
        gd = self.gd
        setattr(gd, name, True)
        self.assertTrue(getattr(gd, name))
        setattr(gd, name, False)
        self.assertFalse(getattr(gd, name))
        self.assertRaises(TypeError, setattr, gd, name, None)

    def _testGetSetDoubleAttr(self, name):
        gd = self.gd
        gd = rdevice.GraphicalDevice()
        setattr(gd, name, 100.0)
        self.assertTrue(getattr(gd, name))
        setattr(gd, name, 0.0)
        self.assertFalse(getattr(gd, name))
        self.assertRaises(TypeError, setattr, gd, name, None)

    def testHasTextUTF8(self):
        self._testGetSetBooleanAttr("hasTextUTF8")

    def testWantSymbolUTF8(self):
        self._testGetSetBooleanAttr("wantSymbolUTF8")
    
    def testLeft(self):
        self._testGetSetDoubleAttr("left")

    def testRight(self):
        self._testGetSetDoubleAttr("right")

    def testTop(self):
        self._testGetSetDoubleAttr("top")

    def testBottom(self):
        self._testGetSetDoubleAttr("bottom")

    def testCanGenMouseDown(self):
        self._testGetSetBooleanAttr("canGenMouseDown")

    def testCanGenMouseMove(self):
        self._testGetSetBooleanAttr("canGenMouseMove")
   
    def testCanGenKeybd(self):
        self._testGetSetBooleanAttr("canGenKeybd")

    def testDisplayListOn(self):
        self._testGetSetBooleanAttr("displayListOn")
  
   
        
class ConcreteDeviceTestCase(unittest.TestCase):
    
    class CodeDevice(rdevice.GraphicalDevice):
        
        def __init__(self, filehandle):
            super(ConcreteDeviceTestCase.CodeDevice, self).__init__()
            self._activated = None
            self._open = True
            self._pagecount = 0
            self._file = filehandle
            
        def activate(self):
            self._activated = True

        def deactivate(self):
            self._activated = False

        def close(self):
            self._activated = None
            self._open = False
            self._file.close()
            
        def size(self, lrbt):
            return (1,2,3,4)

        def newpage(self):
            self._file.write('#--- new page\n')
            self._pagecount = self._pagecount + 1

        def line(self, x1, y1, x2, y2):
            self._file.write('line(%f, %f, %f, %f)' %(x1, y1, x2, y2))

        def polyline(self, x, y):
            self._file.write('polyline(%f, %f)' %(x, y))
            
        def clip(self):
            pass

    def setUp(self):
        #f = tempfile.NamedTemporaryFile()
        f = file('/tmp/foo', mode='w')
        self.gd = ConcreteDeviceTestCase.CodeDevice(f)

    def tearDown(self):
        self.gd.close()

    def testActivate(self):
        self.assertTrue(self.gd._activated)
        #other_gd = ConcreteDeviceTestCase.CodeDevice()
        #self.assertFalse(self.gd._activated)

    def testClose(self):
        self.gd.close()
        self.assertFalse(self.gd._open)

    def testSize(self):
        size = self.gd.size()
        self.assertEquals(size, [1,2,3,4])

    def testLine(self):
        res = rinterface.globalenv.get('plot.new')()
        res = rinterface.globalenv.get('lines')(rinterface.IntSexpVector((0, 0)),
                                                rinterface.IntSexpVector((1, 2)))
        
def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(AbstractDeviceTestCase)
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(ConcreteDeviceTestCase))
    return suite

if __name__ == '__main__':
    tr = unittest.TextTestRunner(verbosity = 2)
    tr.run(suite())
 
