import unittest
import rpy2.robjects as robjects
import rpy2.rinterface as rinterface

from collections import OrderedDict
from datetime import datetime

has_pandas = True
try:
    import pandas
    import numpy
    has_pandas = True
except:
    has_pandas = False

if has_pandas:
    import rpy2.robjects.pandas2ri as rpyp

@unittest.skipUnless(has_pandas, "pandas is not available in python")
class PandasConversionsTestCase(unittest.TestCase):

    def testActivate(self):
        robjects.conversion.py2ri = robjects.default_py2ri
        self.assertNotEqual(rpyp.pandas2ri, robjects.conversion.py2ri)
        rpyp.activate()
        self.assertEqual(rpyp.pandas2ri, robjects.conversion.py2ri)
        rpyp.deactivate()
        self.assertEqual(robjects.default_py2ri, robjects.conversion.py2ri)

    def testActivateTwice(self):
        robjects.conversion.py2ri = robjects.default_py2ri
        self.assertNotEqual(rpyp.pandas2ri, robjects.conversion.py2ri)
        rpyp.activate()
        self.assertEqual(rpyp.pandas2ri, robjects.conversion.py2ri)
        rpyp.activate()
        self.assertEqual(rpyp.pandas2ri, robjects.conversion.py2ri)
        rpyp.deactivate()
        self.assertEqual(robjects.default_py2ri, robjects.conversion.py2ri)
        rpyp.deactivate()
        self.assertEqual(robjects.default_py2ri, robjects.conversion.py2ri)

    def testDataFrame(self):
        l = (('b', numpy.array([True, False, True], dtype=numpy.bool_)),
             ('i', numpy.array([1, 2, 3], dtype="i")),
             ('f', numpy.array([1, 2, 3], dtype="f")),
             ('s', numpy.array(["a", "b", "c"], dtype="S")),
             ('u', numpy.array([u"a", u"b", u"c"], dtype="U")),
             ('dates', [datetime(2012, 5, 2), 
                        datetime(2012, 6, 3), 
                        datetime(2012, 7, 1)]))
        od = OrderedDict(l)
        pd_df = pandas.core.frame.DataFrame(od)
        rp_df = rpyp.pandas2ri(pd_df)
        self.assertEqual(pd_df.shape[0], rp_df.nrow)
        self.assertEqual(pd_df.shape[1], rp_df.ncol)

    def testSeries(self):
        Series = pandas.core.series.Series
        s = Series(numpy.random.randn(5), index=['a', 'b', 'c', 'd', 'e'])
        rp_s = rpyp.pandas2ri(s)
        self.assertEqual(rinterface.SexpVector, type(rp_s))

    def testRepr(self):
        # this should go to testVector, with other tests for repr()
        l = (('b', numpy.array([True, False, True], dtype=numpy.bool_)),
             ('i', numpy.array([1, 2, 3], dtype="i")),
             ('f', numpy.array([1, 2, 3], dtype="f")),
             ('s', numpy.array(["a", "b", "c"], dtype="S")),
             ('u', numpy.array([u"a", u"b", u"c"], dtype="U")))
        od = OrderedDict(l)
        pd_df = pandas.core.frame.DataFrame(od)
        rp_df = rpyp.pandas2ri(pd_df)
        s = repr(rp_df) # used to fail with a TypeError
        s = s.split('\n')
        self.assertEqual('[Array, Array, Array, FactorV..., FactorV...]', s[1].strip())

    def testRi2pandas(self):
        rdataf = robjects.r('data.frame(a=1:2, b=I(c("a", "b")), c=c("a", "b"))')
        pandas_df = rpyp.ri2pandas(rdataf)
        self.assertIsInstance(pandas_df, pandas.DataFrame)
        self.assertEquals(('a', 'b', 'c'), tuple(pandas_df.keys()))
        self.assertEquals(pandas_df['a'].dtype, numpy.dtype('int32'))
        self.assertEquals(pandas_df['b'].dtype, numpy.dtype('O'))
        self.assertEquals(pandas_df['c'].dtype, numpy.dtype('O'))
    
    def testRi2pandas_issue207(self):
        d = robjects.DataFrame({'x': 1})
        rpyp.activate()
        try:
            ok = True
            robjects.globalenv['d'] = d
        except ValueError:
            ok = False
        finally:
            rpyp.deactivate()
            if 'd' in robjects.globalenv:
                del(robjects.globalenv['d'])
        self.assertTrue(ok)

def suite():
    if has_pandas:
        return unittest.TestLoader().loadTestsFromTestCase(PandasConversionsTestCase)
    else:
        return unittest.TestLoader().loadTestsFromTestCase(MissingPandasDummyTestCase)

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

