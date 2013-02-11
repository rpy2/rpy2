import unittest
import rpy2.robjects as robjects

from collections import OrderedDict

try:
    import pandas
    import numpy
    has_pandas = True
    import rpy2.robjects.pandas2ri as rpyp
except:
    has_pandas = False


class MissingPandasDummyTestCase(unittest.TestCase):
    def testMissingPandas(self):
        self.assertTrue(False) # pandas is missing. No tests.

class PandasConversionsTestCase(unittest.TestCase):

    def setUp(self):
        rpyp.activate()

    def tearDown(self):
        robjects.conversion.py2ri = robjects.default_py2ri
        robjects.conversion.ri2py = robjects.default_ri2py

    def testDataFrame(self):
        l = (('b', numpy.array([True, False, True], dtype=numpy.bool_)),
             ('i', numpy.array([1, 2, 3], dtype="i")),
             ('f', numpy.array([1, 2, 3], dtype="f")),
             ('s', numpy.array(["a", "b", "c"], dtype="S")),
             ('u', numpy.array([u"a", u"b", u"c"], dtype="U")))
        od = OrderedDict(l)
        pd_df = pandas.core.frame.DataFrame(od)
        rp_df = robjects.conversion.py2ri(pd_df)
        self.assertEqual(pd_df.shape[0], rp_df.nrow)
        self.assertEqual(pd_df.shape[1], rp_df.ncol)
        

def suite():
    if has_pandas:
        return unittest.TestLoader().loadTestsFromTestCase(PandasConversionsTestCase)
    else:
        return unittest.TestLoader().loadTestsFromTestCase(MissingPandasDummyTestCase)

if __name__ == '__main__':
    unittest.main()

