import unittest
import rpy2.robjects as robjects

from collections import OrderedDict

has_pandas = True
try:
    import pandas
    import numpy
    import rpy2.robjects.pandas2ri as rpyp
except:
    has_pandas = False



@unittest.skipUnless(has_pandas, "pandas is not available in python")
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

    def testSeries(self):
        Series = pandas.core.series.Series
        s = Series(numpy.random.randn(5), index=['a', 'b', 'c', 'd', 'e'])
        rp_s = robjects.conversion.py2ri(s)
        self.assertIsInstance(rp_s, robjects.Array)

    def testRepr(self):
        # this should go to testVector, with other tests for repr()
        l = (('b', numpy.array([True, False, True], dtype=numpy.bool_)),
             ('i', numpy.array([1, 2, 3], dtype="i")),
             ('f', numpy.array([1, 2, 3], dtype="f")),
             ('s', numpy.array(["a", "b", "c"], dtype="S")),
             ('u', numpy.array([u"a", u"b", u"c"], dtype="U")))
        od = OrderedDict(l)
        pd_df = pandas.core.frame.DataFrame(od)
        rp_df = robjects.conversion.py2ri(pd_df)
        s = repr(rp_df) # used to fail with a TypeError
        s = s.split('\n')
        self.assertEqual('[Array, Array, Array, FactorV..., FactorV...]', s[1].strip())

    def testPandas2ri(self):
        # XXX - not a full test, just tests that the function returns the right
        # class. This is currently also the case with some of the tests above
        # (e.g., testSeries)
        rdataf = robjects.r('data.frame(a=1:2, b=c("a", "b"))')
        # Note - I'm following the convention above, but this conflates
        # .activate() with testing the function, so it's not as "unit" as it
        # could be.
        pandas_df = robjects.conversion.ri2py(rdataf)
        self.assertIsInstance(pandas_df, pandas.DataFrame)

def suite():
    if has_pandas:
        return unittest.TestLoader().loadTestsFromTestCase(PandasConversionsTestCase)
    else:
        return unittest.TestLoader().loadTestsFromTestCase(MissingPandasDummyTestCase)

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

