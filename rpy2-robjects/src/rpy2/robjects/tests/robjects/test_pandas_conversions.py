import math
from collections import OrderedDict
from datetime import datetime

import pytest

from rpy2 import rinterface
from rpy2 import robjects
from rpy2.robjects import vectors
from rpy2.robjects import conversion


class MockNamespace(object):
    def __getattr__(self, name):
        return None


has_pandas = False
try:
    import pandas
    has_pandas = True
except:
    pandas = MockNamespace()

has_numpy = False
try:
    import numpy
    has_numpy = True
except:
    numpy = MockNamespace()

if has_pandas:
    import rpy2.robjects.pandas2ri as rpyp

from rpy2.robjects import default_converter
from rpy2.robjects.conversion import localconverter
    
@pytest.mark.skipif(not has_pandas, reason='Package pandas is not installed.')
class TestPandasConversions(object):

    def testActivate(self):
        #FIXME: is the following still making sense ?
        assert rpyp.py2rpy != robjects.conversion.get_conversion().py2rpy
        l = len(robjects.conversion.converter_ctx.get().py2rpy.registry)
        k = set(robjects.conversion.converter_ctx.get().py2rpy.registry.keys())
        rpyp.activate()
        assert len(conversion.converter_ctx.get().py2rpy.registry) > l
        rpyp.deactivate()
        assert len(conversion.converter_ctx.get().py2rpy.registry) == l
        assert set(conversion.converter_ctx.get().py2rpy.registry.keys()) == k

    def testActivateTwice(self):
        #FIXME: is the following still making sense ?
        assert rpyp.py2rpy != robjects.conversion.converter_ctx.get().py2rpy
        l = len(robjects.conversion.converter_ctx.get().py2rpy.registry)
        k = set(robjects.conversion.converter_ctx.get().py2rpy.registry.keys())
        rpyp.activate()
        rpyp.deactivate()
        rpyp.activate()
        assert len(conversion.converter_ctx.get().py2rpy.registry) > l
        rpyp.deactivate()
        assert len(conversion.converter_ctx.get().py2rpy.registry) == l
        assert set(conversion.converter_ctx.get().py2rpy.registry.keys()) == k

    @pytest.mark.parametrize(
        'cls',
        (robjects.ListVector,
         rinterface.ListSexpVector)
    )
    def test_list(self, cls):
        rlist = cls(robjects.ListVector({'a': 1, 'b': 'c'}))
        with localconverter(default_converter + rpyp.converter) as cv:
            pylist = cv.rpy2py(rlist)
        assert len(pylist) == 2
        assert set(pylist.keys()) == set(rlist.names)

    def test_dataframe(self):
        # Content for test data frame
        l = (
            ('b', numpy.array([True, False, True], dtype=numpy.bool_)),
            ('i', numpy.array([1, 2, 3], dtype='i')),
            ('f', numpy.array([1, 2, 3], dtype='f')),
            # ('s', numpy.array([b'b', b'c', b'd'], dtype='S1')),
            ('u', numpy.array([u'a', u'b', u'c'], dtype='U')),
            ('dates', [datetime(2012, 5, 2), 
                       datetime(2012, 6, 3), 
                       datetime(2012, 7, 1)])
        )
        od = OrderedDict(l)
        # Pandas data frame
        pd_df = pandas.core.frame.DataFrame(od)
        # Convert to R
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_df = robjects.conversion.converter_ctx.get().py2rpy(pd_df)
        assert pd_df.shape[0] == rp_df.nrow
        assert pd_df.shape[1] == rp_df.ncol
        # assert tuple(rp_df.rx2('s')) == (b'b', b'c', b'd')
        assert tuple(rp_df.rx2('u')) == ('a', 'b', 'c')

    def test_dataframe_columnnames(self):
        pd_df = pandas.DataFrame({'the one': [1, 2], 'the other': [3, 4]})
        # Convert to R
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_df = robjects.conversion.converter_ctx.get().py2rpy(pd_df)
        assert tuple(rp_df.names) == ('the one', 'the other')

    def test_dataframe_warns_duplicated_index(self):
        pd_df = pandas.DataFrame({'x': [1, 2]}, index=['a', 'a'])
        with pytest.warns(
            UserWarning,
            match='DataFrame contains duplicated elements in the index'
        ) as record:
            with localconverter(default_converter + rpyp.converter) as cv:
                robjects.conversion.converter_ctx.get().py2rpy(pd_df)
        assert len(record) == 1

    def test_series(self):
        Series = pandas.core.series.Series
        s = Series(numpy.random.randn(5), index=['a', 'b', 'c', 'd', 'e'])
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_s = robjects.conversion.converter_ctx.get().py2rpy(s)
        assert isinstance(rp_s, rinterface.FloatSexpVector)

    @pytest.mark.parametrize('dtype',
                             ('i',
                              numpy.int32 if has_pandas else None,
                              numpy.int8 if has_pandas else None,
                              numpy.int16 if has_pandas else None,
                              numpy.int32 if has_pandas else None,
                              numpy.int64 if has_pandas else None,
                              numpy.uint8 if has_pandas else None,
                              numpy.uint16 if has_pandas else None,
                              pandas.Int32Dtype if has_pandas else None,
                              pandas.Int64Dtype if has_pandas else None))
    def test_series_int(self, dtype):
        Series = pandas.core.series.Series
        s = Series(range(5),
                   index=['a', 'b', 'c', 'd', 'e'],
                   dtype=dtype)
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_s = robjects.conversion.get_conversion().py2rpy(s)
        assert isinstance(rp_s, rinterface.IntSexpVector)

    @pytest.mark.parametrize('dtype',
                             (pandas.Int32Dtype() if has_pandas else None,
                              pandas.Int64Dtype() if has_pandas else None))
    def test_dataframe_int_nan(self, dtype):
        a = pandas.DataFrame([(numpy.nan,)], dtype=dtype, columns=['z'])
        with localconverter(default_converter + rpyp.converter) as cv:
            b = robjects.conversion.get_conversion().py2rpy(a)
        assert b[0][0] is rinterface.na_values.NA_Integer
        with localconverter(default_converter + rpyp.converter) as cv:
            c = robjects.conversion.get_conversion().rpy2py(b)

    @pytest.mark.parametrize('dtype', (pandas.Int32Dtype() if has_pandas else None,
                                       pandas.Int64Dtype() if has_pandas else None))
    def test_series_int_nan(self, dtype):
        a = pandas.Series((numpy.nan,), dtype=dtype, index=['z'])
        with localconverter(default_converter + rpyp.converter) as _:
            b = robjects.conversion.converter_ctx.get().py2rpy(a)
        assert b[0] is rinterface.na_values.NA_Integer
        with localconverter(default_converter + rpyp.converter) as _:
            c = robjects.conversion.converter_ctx.get().rpy2py(b)

    @pytest.mark.skipif(not (has_numpy and has_pandas),
                        reason='Packages numpy and pandas must be installed.')
    @pytest.mark.parametrize(
        'data',
        (['x', 'y', 'z'],
         ['x', 'y', None],
         ['x', 'y', numpy.nan],
         ['x', 'y', pandas.NA])
    )
    @pytest.mark.parametrize(
        'dtype', ['O', pandas.StringDtype() if has_pandas else None]
    )
    def test_series_obj_str(self, data, dtype):
        Series = pandas.core.series.Series
        s = Series(data, index=['a', 'b', 'c'], dtype=dtype)
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_s = robjects.conversion.converter_ctx.get().py2rpy(s)
        assert isinstance(rp_s, rinterface.StrSexpVector)

    def test_series_obj_mixed(self):
        Series = pandas.core.series.Series
        s = Series(['x', 1, False], index=['a', 'b', 'c'])
        with localconverter(default_converter + rpyp.converter) as cv:
            with pytest.raises(ValueError):
                rp_s = robjects.conversion.converter_ctx.get().py2rpy(s)

        s = Series(['x', 1, None], index=['a', 'b', 'c'])
        with localconverter(default_converter + rpyp.converter) as cv:
            with pytest.raises(ValueError):
                rp_s = robjects.conversion.converter_ctx.get().py2rpy(s)

    @pytest.mark.skipif(not has_pandas,
                        reason='pandas must be installed.')
    @pytest.mark.parametrize(
        'data',
        ([True, False, True],
         [True, False, None])
    )
    @pytest.mark.parametrize(
        'dtype', [bool, pandas.BooleanDtype() if has_pandas else None]
    )
    @pytest.mark.parametrize(
        'constructor,wrapcheck',
        [(pandas.Series, lambda x: x),
         (pandas.DataFrame, lambda x: x[0])]
    )
    def test_series_obj_bool(self, data, dtype, constructor, wrapcheck):
        s = constructor(data, index=['a', 'b', 'c'], dtype=dtype)
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_s = robjects.conversion.converter_ctx.get().py2rpy(s)
        assert isinstance(wrapcheck(rp_s), rinterface.BoolSexpVector)


    @pytest.mark.parametrize(
        'data',
        ([1.1, 2.2, 3.3],
         [1.1, 2.2, None])
    )
    @pytest.mark.parametrize(
        'dtype', [float, pandas.Float64Dtype() if has_pandas else None]
    )
    def test_series_obj_float(self, data, dtype):
        Series = pandas.core.series.Series
        s = Series(data, index=['a', 'b', 'c'], dtype=dtype)
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_s = robjects.conversion.converter_ctx.get().py2rpy(s)
        assert isinstance(rp_s, rinterface.FloatSexpVector)


    def test_series_obj_allnone(self):
        Series = pandas.core.series.Series
        s = Series([None, None, None], index=['a', 'b', 'c'])
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_s = robjects.conversion.converter_ctx.get().py2rpy(s)
        assert isinstance(rp_s, rinterface.BoolSexpVector)


    def test_series_issue264(self):
        Series = pandas.core.series.Series
        s = Series(('a', 'b', 'c', 'd', 'e'),
                   index=pandas.Index([0,1,2,3,4], dtype='int64'))
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_s = robjects.conversion.converter_ctx.get().py2rpy(s)
        # segfault before the fix
        str(rp_s)
        assert isinstance(rp_s, rinterface.StrSexpVector)

    def test_object2String(self):
        series = pandas.Series(['a', 'b', 'c', 'a'], dtype='O')
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_c = robjects.conversion.converter_ctx.get().py2rpy(series)
            assert isinstance(rp_c, rinterface.StrSexpVector)

    def test_object2String_with_None(self):
        series = pandas.Series([None, 'a', 'b', 'c', 'a'], dtype='O')
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_c = robjects.conversion.converter_ctx.get().py2rpy(series)
            assert isinstance(rp_c, rinterface.StrSexpVector)

    def test_factor2Category(self):
        factor = robjects.vectors.FactorVector(('a', 'b', 'a'))
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_c = robjects.conversion.converter_ctx.get().rpy2py(factor)
        assert isinstance(rp_c, pandas.Categorical)

    def test_factorwithNA2Category(self):
        factor = robjects.vectors.FactorVector(('a', 'b', 'a', None))
        assert factor[3] is rinterface.na_values.NA_Integer
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_c = robjects.conversion.converter_ctx.get().rpy2py(factor)
        assert isinstance(rp_c, pandas.Categorical)
        assert math.isnan(rp_c[3])

    def test_orderedFactor2Category(self):
        factor = robjects.vectors.FactorVector(('a', 'b', 'a'), ordered=True)
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_c = robjects.conversion.converter_ctx.get().rpy2py(factor)
        assert isinstance(rp_c, pandas.Categorical)

    def test_category2Factor(self):
        category = pandas.Series(["a","b","c","a"], dtype="category")
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_c = robjects.conversion.converter_ctx.get().py2rpy(category)
            assert isinstance(rp_c, robjects.vectors.FactorVector)

    def test_categorywithNA2Factor(self):
        category = pandas.Series(['a', 'b', 'c', numpy.nan], dtype='category')
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_c = robjects.conversion.converter_ctx.get().py2rpy(category)
            assert isinstance(rp_c, robjects.vectors.FactorVector)
        assert rp_c[3] == rinterface.NA_Integer

    def test_orderedCategory2Factor(self):
        category = pandas.Series(pandas.Categorical(['a','b','c','a'],
                                                    categories=['a','b','c'],
                                                    ordered=True))
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_c = robjects.conversion.converter_ctx.get().py2rpy(category)
            assert isinstance(rp_c, robjects.vectors.FactorVector)

    def test_datetime2posixct(self):
        datetime = pandas.Series(
            pandas.date_range('2017-01-01 00:00:00.234',
                              periods=20, freq='ms', tz='UTC')
        )
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_c = robjects.conversion.converter_ctx.get().py2rpy(datetime)
            assert isinstance(rp_c, robjects.vectors.POSIXct)
            assert int(rp_c[0]) == 1483228800
            assert int(rp_c[1]) == 1483228800
            assert rp_c[0] != rp_c[1]

    def test_datetime2posixct_withNA(self):
        datetime = pandas.Series(
            pandas.date_range('2017-01-01 00:00:00.234',
                              periods=20, freq='ms', tz='UTC')
        )
        datetime[1] = pandas.NaT
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_c = robjects.conversion.converter_ctx.get().py2rpy(datetime)
            assert isinstance(rp_c, robjects.vectors.POSIXct)
            assert int(rp_c[0]) == 1483228800
            assert math.isnan(rp_c[1])

    def test_date2posixct(self):
        today = datetime.now().date()
        date = pandas.Series([today])
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_c = robjects.conversion.converter_ctx.get().py2rpy(date)
            assert isinstance(rp_c, robjects.vectors.FloatSexpVector)
            assert tuple(int(x) for x in rp_c) == (today.toordinal(), )

    def test_timeR2Pandas(self):
        tzone = robjects.vectors.get_timezone()
        dt = [datetime(1960, 5, 2),
              datetime(1970, 6, 3), 
              datetime(2012, 7, 1)]
        dt = [x.replace(tzinfo=tzone) for x in dt]
        # fix the time
        ts = [x.timestamp() for x in dt]
        # Create an R POSIXct vector.
        r_time = robjects.baseenv['as.POSIXct'](
            rinterface.FloatSexpVector(ts),
            origin=rinterface.StrSexpVector(('1970-01-01',))
        )

        # Convert R POSIXct vector to pandas-compatible vector
        with localconverter(default_converter + rpyp.converter) as cv:
            py_time = robjects.conversion.converter_ctx.get().rpy2py(r_time)

        # Check that the round trip did not introduce changes
        for expected, obtained in zip(dt, py_time):
            assert expected == obtained.to_pydatetime()

        # Try with NA.
        r_time[1] = rinterface.na_values.NA_Real
        # Convert R POSIXct vector to pandas-compatible vector
        with localconverter(default_converter + rpyp.converter) as cv:
            py_time = robjects.conversion.converter_ctx.get().rpy2py(r_time)

        assert py_time[1] is pandas.NaT

    def test_posixct_in_dataframe_to_pandas(self):
        tzone = robjects.vectors.get_timezone()
        dt = [datetime(1960, 5, 2),
              datetime(1970, 6, 3), 
              datetime(2012, 7, 1)]
        dt = [x.replace(tzinfo=tzone) for x in dt]
        # fix the time
        ts = [x.timestamp() for x in dt]
        # Create an R data.frame with a posixct_vector.
        r_dataf = robjects.vectors.DataFrame({
            'mydate': robjects.baseenv['as.POSIXct'](
                rinterface.FloatSexpVector(ts),
                origin=rinterface.StrSexpVector(('1970-01-01',))
            )})

        # Convert R POSIXct vector to pandas-compatible vector
        with localconverter(default_converter + rpyp.converter):
            py_dataf = robjects.conversion.converter_ctx.get().rpy2py(r_dataf)
        assert pandas.core.dtypes.common.is_datetime64_any_dtype(py_dataf['mydate'])

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
            rp_df = robjects.conversion.converter_ctx.get().py2rpy(pd_df)
        s = repr(rp_df)  # used to fail with a TypeError.
        s = s.split('\n')
        repr_str = ('[BoolSex..., IntSexp..., FloatSe..., '
                    'ByteSex..., StrSexp...]')
        assert repr_str == s[2].strip()

        # Try again with the conversion still active.
        with localconverter(default_converter + rpyp.converter) as cv:
            rp_df = robjects.conversion.converter_ctx.get().py2rpy(pd_df)
            s = repr(rp_df)  # used to fail with a TypeError.
        s = s.split('\n')
        assert repr_str == s[2].strip()

    @pytest.mark.parametrize(
        'colnames',
        (('w', 'x', 'y', 'z'),
         ('w', 'x', 'y', 'x'))
    )
    @pytest.mark.parametrize(
        'r_rownames,py_rownames',
        (('NULL', ('1', '2')),
         ('c("a", "b")',('a', 'b')))
    )
    def test_ri2pandas(self, r_rownames, py_rownames, colnames):
        rdataf = robjects.r(
            f'data.frame({colnames[0]}=1:2, '
            f'           {colnames[1]}=1:2, '
            f'           {colnames[2]}=I(c("a", "b")), '
            f'           {colnames[3]}=factor(c("a", "b")), '
            f'           row.names={r_rownames}, '
            '            check.names=FALSE)')
        with localconverter(default_converter + rpyp.converter) as cv:
            pandas_df = robjects.conversion.converter_ctx.get().rpy2py(rdataf)

        assert isinstance(pandas_df, pandas.DataFrame)
        assert colnames == tuple(pandas_df.keys())
        assert pandas_df['w'].dtype in (numpy.dtype('int32'),
                                        numpy.dtype('int64'))
        assert pandas_df['y'].dtype == numpy.dtype('O')
        if 'z' in colnames:
            assert isinstance(pandas_df['z'].dtype,
                              pandas.api.types.CategoricalDtype)
        assert tuple(pandas_df.index) == py_rownames

    @pytest.mark.parametrize(
        'rcode,names,values',
        (
            ('list(list(x=1, y=3), list(x=2, y=4))',
             ('x', 'y'), ((1, 2), (3, 4))),
            ('list(list(x=1), list(x=2, y=4))',
             ('x', 'y'), ((1, 2), (None, 4)))
        )
    )
    def test__records_to_columns(self, rcode, names, values):
        rlist = robjects.r(rcode)
        columns = rpyp._records_to_columns(rlist)
        assert tuple(columns.keys()) == names
        for n, v in zip(names, values):
            assert tuple(columns[n]) == v

    @pytest.mark.parametrize(
        'rcode,names,values',
        (
            ('data.frame('
             '  a = c("a", "b"),'
             '  b = c(1, 2)'
             ')',
             ('a', 'b'),
             (["a", "b"], [1, 2])),
            ('data.frame('
             '  a = c("a", "b"),'
             '  b = I(list(list(x=1, y=3), list(x=2, y=4)))'
             ')',
             ('a', ('b', 'x'), ('b', 'y')),
             (["a", "b"], [1, 2], [3, 4]))
        )
    )
    def test__flatten_dataframe(self, rcode, names, values):
        rdataf = robjects.r(rcode)
        colnames_lst = []
        columns = tuple(rpyp._flatten_dataframe(rdataf, colnames_lst))
        assert tuple(colnames_lst) == names

    @pytest.mark.parametrize(
        'rcode,names,values',
        (
            ('data.frame('
             '  a = c("a", "b"),'
             '  b = I(list(list(x=1, y=3), list(x=2, y=4)))'
             ')',
             ('a', ('b', 'x'), ('b', 'y')),
             (["a", "b"], [1, 2], [3, 4])),
            ('data.frame('
             '  b = I(list(list(x=1, y=3), list(x=2, y=4)))'
             ')',
             (('b', 'x'), ('b', 'y')),
             ([1, 2], [3, 4])),
            ('aggregate(gear ~ am, mtcars, '
             'function(x) c(mean = mean(x), sd = sd(x)), '
             'simplify=FALSE)',
             ('am', ('gear', 'mean'), ('gear', 'sd')),
             ([0.0, 1.0], [3.210526, 4.384615],
              [0.418854, 0.506370]))
        )
    )
    def test_dataframe_with_list(self, rcode, names, values):
        rdataf = robjects.r(rcode)
        with localconverter(default_converter + rpyp.converter) as cv:
            pandas_df = robjects.conversion.converter_ctx.get().rpy2py(rdataf)
        assert tuple(pandas_df.columns) == names

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
