import unittest
import rpy2.rinterface as rinterface
import rpy2.rinterface.rpy_device as rdevice
import sys, os, subprocess, time, tempfile, signal

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
    pass

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(AbstractDeviceTestCase)
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(ConcreteDeviceTestCase))
    return suite

if __name__ == '__main__':
     unittest.main()
