import pytest
import pytz
import sys
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

from rpy2.robjects import default_converter
from rpy2.robjects.conversion import Converter, localconverter
    
@pytest.mark.skipif(not has_pandas, reason='Package pandas is not installed.')
class TestPandasConversions(object):

    def testActivate(self):
        #FIXME: is the following still making sense ?
        assert rpyp.py2rpy != robjects.conversion.py2rpy
        l = len(robjects.conversion.py2rpy.registry)
        k = set(robjects.conversion.py2rpy.registry.keys())
        rpyp.activate()
        assert len(conversion.py2rpy.registry) > l
        rpyp.deactivate()
        assert len(conversion.py2rpy.registry) == l
        assert set(conversion.py2rpy.registry.keys()) == k

    def testActivateTwice(self):
        #FIXME: is the following still making sense ?
        assert rpyp.py2rpy != robjects.conversion.py2rpy
        l = len(robjects.conversion.py2rpy.registry)
        k = set(robjects.conversion.py2rpy.registry.keys())
        rpyp.activate()
        rpyp.deactivate()
        rpyp.activate()
        assert len(conversion.py2rpy.registry) > l
        rpyp.deactivate()
        assert len(conversion.py2rpy.registry) == l
        assert set(conversion.py2rpy.registry.keys()) == k

    @pytest.mark.skip(reason='segfault')
    def test_dataframe(self):
        # Content for test data frame
        l = (('b', numpy.array([True, False, True], dtype=numpy.bool_)),
             ('i', numpy.array([1, 2, 3], dtype="i")),
             ('f', numpy.array([1, 2, 3], dtype="f")),
             ('s', numpy.array(["b", "c", "d"], dtype="S")),
             ('u', numpy.array([u"a", u"b", u"c"], dtype="U")),
             ('dates', [datetime(2012, 5, 2), 
                        datetime(2012, 6, 3), 
                        datetime(2012, 7, 1)]))
        od = OrderedDict(l)
        # Pandas data frame
        pd_df = pandas.core.frame.DataFrame(od)
        # Convert to R
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_df = robjects.conversion.py2rpy(pd_df)
        assert pd_df.shape[0] == rp_df.nrow
        assert pd_df.shape[1] == rp_df.ncol
        assert tuple(rp_df.rx2('s')) == (b"b", b"c", b"d")
            
    def test_series(self):
        Series = pandas.core.series.Series
        s = Series(numpy.random.randn(5), index=['a', 'b', 'c', 'd', 'e'])
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_s = robjects.conversion.py2rpy(s)
        assert rinterface.FloatSexpVector == type(rp_s)

    def test_series_issue264(self):
        Series = pandas.core.series.Series
        s = Series(('a', 'b', 'c', 'd', 'e'),
                   index=pandas.Int64Index([0,1,2,3,4]))
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_s = robjects.conversion.py2rpy(s)
        # segfault before the fix
        str(rp_s)
        assert rinterface.StrSexpVector == type(rp_s)

    def test_object2String(self):
        series = pandas.Series(["a","b","c","a"], dtype="O")
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_c = robjects.conversion.py2rpy(series)
            assert robjects.vectors.StrVector == type(rp_c)

    def test_factor2Category(self):
        factor = robjects.vectors.FactorVector(('a', 'b', 'a'))
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_c = robjects.conversion.rpy2py(factor)
        assert pandas.Categorical == type(rp_c)

    @pytest.mark.skip(reason='segfault')
    def test_orderedFactor2Category(self):
        factor = robjects.vectors.FactorVector(('a', 'b', 'a'), ordered=True)
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_c = robjects.conversion.rpy2py(factor)
        assert pandas.Categorical == type(rp_c)

    @pytest.mark.skip(reason='segfault')
    def test_category2Factor(self):
        category = pandas.Series(["a","b","c","a"], dtype="category")
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_c = robjects.conversion.py2rpy(category)
            assert robjects.vectors.FactorVector == type(rp_c)

    def test_orderedCategory2Factor(self):
        category = pandas.Series(pandas.Categorical(['a','b','c','a'],
                                                    categories=['a','b','c'],
                                                    ordered=True))
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_c = robjects.conversion.py2rpy(category)
            assert robjects.vectors.FactorVector == type(rp_c)

    def test_timeR2Pandas(self):
        tzone = rpyp.get_timezone()
        dt = [datetime(1960, 5, 2),
              datetime(1970, 6, 3), 
              datetime(2012, 7, 1)]
        dt = [x.replace(tzinfo=tzone) for x in dt]
        # fix the time
        ts = [x.timestamp() for x in dt]
        # Create an R POSIXct vector.
        r_time = robjects.baseenv['as.POSIXct'](rinterface.FloatSexpVector(ts),
                                                origin=rinterface.StrSexpVector(('1970-01-01',)))

        # Convert R POSIXct vector to pandas-compatible vector
        with localconverter(default_converter + rpyp.converter) as cv:
            py_time = robjects.conversion.rpy2py(r_time)

        # Check that the round trip did not introduce changes
        for expected, obtained in zip(dt, py_time):
            assert expected == obtained.to_pydatetime()

    def test_repr(self):
        # this should go to testVector, with other tests for repr()
        l = (('b', numpy.array([True, False, True], dtype=numpy.bool_)),
             ('i', numpy.array([1, 2, 3], dtype="i")),
             ('f', numpy.array([1, 2, 3], dtype="f")),
             ('s', numpy.array(["a", "b", "c"], dtype="S")),
             ('u', numpy.array([u"a", u"b", u"c"], dtype="U")))
        od = OrderedDict(l)
        pd_df = pandas.core.frame.DataFrame(od)
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_df = robjects.conversion.py2rpy(pd_df)
        s = repr(rp_df) # used to fail with a TypeError
        s = s.split('\n')
        repr_str = '[BoolVec..., IntVector, FloatVe..., Vector, StrVector]'
        assert repr_str == s[2].strip()

    def test_ri2pandas(self):
        rdataf = robjects.r('data.frame(a=1:2, '
                            '           b=I(c("a", "b")), '
                            '           c=c("a", "b"))')
        with localconverter(default_converter + rpyp.converter) as cv:
            pandas_df = robjects.conversion.rpy2py(rdataf)

        assert isinstance(pandas_df, pandas.DataFrame)
        assert ('a', 'b', 'c') == tuple(pandas_df.keys())
        assert pandas_df['a'].dtype == numpy.dtype('int32')
        assert pandas_df['b'].dtype == numpy.dtype('O')
        assert isinstance(pandas_df['c'].dtype,
                          pandas.api.types.CategoricalDtype)

    def test_ri2pandas_issue207(self):
        d = robjects.DataFrame({'x': 1})
        with localconverter(default_converter + rpyp.converter) as cv:
            try:
                ok = True
                robjects.globalenv['d'] = d
            except ValueError:
                ok = False
            finally:
                if 'd' in robjects.globalenv:
                    del(robjects.globalenv['d'])
        assert ok
