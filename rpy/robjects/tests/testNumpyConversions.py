import unittest
import rpy2.robjects as robjects
r = robjects.r

try:
    import numpy
    has_numpy = True
    import rpy2.robjects.numpy2ri as rpyn
except:
    has_numpy = False


class MissingNumpyDummyTestCase(unittest.TestCase):
    def testMissingNumpy(self):
        self.assertTrue(False) # numpy is missing. No tests.

class NumpyConversionsTestCase(unittest.TestCase):

    def setUp(self):
        robjects.conversion.py2ri = rpyn.numpy2ri

    def tearDown(self):
        robjects.conversion.py2ri = robjects.default_py2ri

    def checkHomogeneous(self, obj, mode, storage_mode):
        converted = robjects.conversion.py2ri(obj)
        self.assertEquals(r["mode"](converted)[0], mode)
        self.assertEquals(r["storage.mode"](converted)[0], storage_mode)
        self.assertEquals(list(obj), list(converted))
        self.assertTrue(r["is.array"](converted)[0])

    def testVectorBoolean(self):
        b = numpy.array([True, False, True], dtype=numpy.bool_)
        self.checkHomogeneous(b, "logical", "logical")

    def testVectorInteger(self):
        i = numpy.array([1, 2, 3], dtype="i")
        self.checkHomogeneous(i, "numeric", "integer")

    def testVectorFloat(self):
        f = numpy.array([1, 2, 3], dtype="f")
        self.checkHomogeneous(f, "numeric", "double")

    def testVectorComplex(self):
        c = numpy.array([1j, 2j, 3j], dtype=numpy.complex_)
        self.checkHomogeneous(c, "complex", "complex")

    def testVectorCharacter(self):
        s = numpy.array(["a", "b", "c"], dtype="S")
        self.checkHomogeneous(s, "character", "character")

    def testVectorUnicodeCharacter(self):
        u = numpy.array([u"a", u"b", u"c"], dtype="U")
        self.checkHomogeneous(u, "character", "character")

    def testArray(self):

        i2d = numpy.array([[1, 2, 3], [4, 5, 6]], dtype="i")
        i2d_r = robjects.conversion.py2ri(i2d)

        self.assertEquals(r["storage.mode"](i2d_r)[0], "integer")
        self.assertEquals(tuple(r["dim"](i2d_r)), (2, 3))

        # Make sure we got the row/column swap right:
        self.assertEquals(i2d_r.rx(1, 2)[0], i2d[0, 1])

        f3d = numpy.arange(24, dtype="f").reshape((2, 3, 4))
        f3d_r = robjects.conversion.py2ri(f3d)

        self.assertEquals(r["storage.mode"](f3d_r)[0], "double")
        self.assertEquals(tuple(r["dim"](f3d_r)), (2, 3, 4))

        # Make sure we got the row/column swap right:
        self.assertEquals(f3d_r.rx(1, 2, 3)[0], f3d[0, 1, 2])

    def testObjectArray(self):
        o = numpy.array([1, "a", 3.2], dtype=numpy.object_)
        o_r = robjects.conversion.py2ri(o)
        self.assertEquals(r["mode"](o_r)[0], "list")
        self.assertEquals(r["[["](o_r, 1)[0], 1)
        self.assertEquals(r["[["](o_r, 2)[0], "a")
        self.assertEquals(r["[["](o_r, 3)[0], 3.2)

    def testRecordArray(self):
        rec = numpy.array([(1, 2.3), (2, -0.7), (3, 12.1)],
                          dtype=[("count", "i"), ("value", numpy.double)])
        rec_r = robjects.conversion.py2ri(rec)
        self.assertTrue(r["is.data.frame"](rec_r)[0])
        self.assertEquals(tuple(r["names"](rec_r)), ("count", "value"))
        count_r = r["$"](rec_r, "count")
        value_r = r["$"](rec_r, "value")
        self.assertEquals(r["storage.mode"](count_r)[0], "integer")
        self.assertEquals(r["storage.mode"](value_r)[0], "double")
        self.assertEquals(count_r[1], 2)
        self.assertEquals(value_r[2], 12.1)

    def testBadArray(self):
        u = numpy.array([1, 2, 3], dtype=numpy.uint32)
        self.assertRaises(ValueError, robjects.conversion.py2ri, u)

    def testAssignNumpyObject(self):
        x = numpy.arange(-10., 10., 1)
        env = robjects.Environment()
        env["x"] = x
        self.assertEquals(1, len(env))
        self.assertTrue(isinstance(env["x"], robjects.Array))

def suite():
    if has_numpy:
        return unittest.TestLoader().loadTestsFromTestCase(NumpyConversionsTestCase)
    else:
        return unittest.TestLoader().loadTestsFromTestCase(MissingNumpyDummyTestCase)

if __name__ == '__main__':
    unittest.main()

