import unittest
import rpy2.robjects as robjects
from rpy2.robjects import conversion
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

@unittest.skipUnless(has_pandas, "The Python package is not installed: functionalities associated with it cannot be tested.")
class PandasConversionsTestCase(unittest.TestCase):

    def testActivate(self):
        robjects.conversion.py2ri = robjects.default_py2ri
        #FIXME: is the following still making sense ?
        self.assertNotEqual(rpyp.py2ri, robjects.conversion.py2ri)
        l = len(robjects.conversion.py2ri.registry)
        k = set(robjects.conversion.py2ri.registry.keys())
        rpyp.activate()
        self.assertTrue(len(conversion.py2ri.registry) > l)
        rpyp.deactivate()
        self.assertEqual(l, len(conversion.py2ri.registry))
        self.assertEqual(k, set(conversion.py2ri.registry.keys()))

    def testActivateTwice(self):
        robjects.conversion.py2ri = robjects.default_py2ri
        #FIXME: is the following still making sense ?
        self.assertNotEqual(rpyp.py2ri, robjects.conversion.py2ri)
        l = len(robjects.conversion.py2ri.registry)
        k = set(robjects.conversion.py2ri.registry.keys())
        rpyp.activate()
        rpyp.deactivate()
        rpyp.activate()
        self.assertTrue(len(conversion.py2ri.registry) > l)
        rpyp.deactivate()
        self.assertEqual(l, len(conversion.py2ri.registry))
        self.assertEqual(k, set(conversion.py2ri.registry.keys()))

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
        rpyp.activate()
        rp_df = robjects.conversion.py2ri(pd_df)
        rpyp.deactivate()
        self.assertEqual(pd_df.shape[0], rp_df.nrow)
        self.assertEqual(pd_df.shape[1], rp_df.ncol)

    def testSeries(self):
        Series = pandas.core.series.Series
        s = Series(numpy.random.randn(5), index=['a', 'b', 'c', 'd', 'e'])
        rpyp.activate()
        rp_s = robjects.conversion.py2ri(s)
        rpyp.deactivate()
        self.assertEqual(rinterface.FloatSexpVector, type(rp_s))

    def testSeries_issue264(self):
        Series = pandas.core.series.Series
        s = Series(('a', 'b', 'c', 'd', 'e'),
                   index=pandas.Int64Index([0,1,2,3,4]))
        rpyp.activate()
        rp_s = robjects.conversion.py2ri(s)
        rpyp.deactivate()
        # segfault before the fix
        str(rp_s)
        self.assertEqual(rinterface.ListSexpVector, type(rp_s))

    def testCategorical(self):
        factor = robjects.vectors.FactorVector(('a', 'b', 'a'))
        rpyp.activate()
        rp_c = robjects.conversion.ri2py(factor)
        rpyp.deactivate()
        self.assertEqual(pandas.Categorical, type(rp_c))

    def testRepr(self):
        # this should go to testVector, with other tests for repr()
        l = (('b', numpy.array([True, False, True], dtype=numpy.bool_)),
             ('i', numpy.array([1, 2, 3], dtype="i")),
             ('f', numpy.array([1, 2, 3], dtype="f")),
             ('s', numpy.array(["a", "b", "c"], dtype="S")),
             ('u', numpy.array([u"a", u"b", u"c"], dtype="U")))
        od = OrderedDict(l)
        pd_df = pandas.core.frame.DataFrame(od)
        rpyp.activate()
        rp_df = robjects.conversion.py2ri(pd_df)
        rpyp.deactivate()
        s = repr(rp_df) # used to fail with a TypeError
        s = s.split('\n')
        self.assertEqual('[Array, Array, Array, FactorV..., FactorV...]', s[1].strip())

    def testRi2pandas(self):
        rdataf = robjects.r('data.frame(a=1:2, b=I(c("a", "b")), c=c("a", "b"))')
        rpyp.activate()
        pandas_df = robjects.conversion.ri2py(rdataf)
        rpyp.deactivate()
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

