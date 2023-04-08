"""This module handles the conversion of data structures
between R objects handled by rpy2 and pandas objects."""

import rpy2.robjects.conversion as conversion
import rpy2.rinterface as rinterface
from rpy2.rinterface_lib import na_values
from rpy2.rinterface import IntSexpVector
from rpy2.rinterface import ListSexpVector
from rpy2.rinterface import SexpVector
from rpy2.rinterface import StrSexpVector

import datetime
import functools
import math
import numpy  # type: ignore
import pandas  # type: ignore
import pandas.core.series  # type: ignore
from pandas.core.frame import DataFrame as PandasDataFrame  # type: ignore
from pandas.core.dtypes.api import is_datetime64_any_dtype  # type: ignore
import warnings

from collections import OrderedDict
from rpy2.robjects.vectors import (BoolVector,
                                   DataFrame,
                                   DateVector,
                                   FactorVector,
                                   FloatVector,
                                   FloatSexpVector,
                                   StrVector,
                                   IntVector,
                                   POSIXct)

# The pandas converter requires numpy.
import rpy2.robjects.numpy2ri as numpy2ri

original_converter = None

ISOdatetime = rinterface.baseenv['ISOdatetime']
as_vector = rinterface.baseenv['as.vector']

converter = conversion.Converter('original pandas conversion')
py2rpy = converter.py2rpy
rpy2py = converter.rpy2py

# numpy types for Pandas columns that require (even more) special handling
dt_O_type = numpy.dtype('O')

# pandas types for series of integer (optional missing) values.
integer_array_types = ('Int8', 'Int16', 'Int32', 'Int64', 'UInt8',
                       'UInt16', 'UInt32', 'UInt64')


@py2rpy.register(PandasDataFrame)
def py2rpy_pandasdataframe(obj):
    if obj.index.duplicated().any():
        warnings.warn('DataFrame contains duplicated elements in the index, '
                      'which will lead to loss of the row names in the '
                      'resulting data.frame')

    od = OrderedDict()
    for name, values in obj.items():
        try:
            od[name] = conversion.converter_ctx.get().py2rpy(values)
        except Exception as e:
            warnings.warn('Error while trying to convert '
                          'the column "%s". Fall back to string conversion. '
                          'The error is: %s'
                          % (name, str(e)))
            od[name] = conversion.converter_ctx.get().py2rpy(
                values.astype('string')
            )

    return DataFrame(od)


@py2rpy.register(pandas.Index)
def py2rpy_pandasindex(obj):
    if obj.dtype.kind == 'O':
        return StrVector(obj)
    else:
        # pandas2ri should definitely not have to know which paths remain to be
        # converted by numpy2ri
        # Answer: the thing is that pandas2ri builds on the conversion
        # rules defined by numpy2ri - deferring to numpy2ri is allowing
        # us to reuse that code.
        return numpy2ri.numpy2rpy(obj)


@py2rpy.register(pandas.Categorical)
def py2rpy_categorical(obj):
    for c in obj.categories:
        if not isinstance(c, str):
            raise ValueError('Converting pandas "Category" series to '
                             'R factor is only possible when categories '
                             'are strings.')
    res = IntSexpVector(list(rinterface.NA_Integer if x == -1 else x+1
                             for x in obj.codes))
    res.do_slot_assign('levels', StrSexpVector(obj.categories))
    if obj.ordered:
        res.rclass = StrSexpVector(('ordered', 'factor'))
    else:
        res.rclass = StrSexpVector(('factor',))
    return res


def py2rpy_categoryseries(obj):
    warnings.warn('Use py2rpy_categorical(obj.cat).', DeprecationWarning)
    return py2rpy_categorical(obj.cat)


def _populate_r_vector_with_na(na_value):
    def f(iterable, r_vector,
          set_elt,
          cast_value):
        for i, v in enumerate(iterable):
            if (
                    v is None
                    or
                    v is pandas.NA
                    or
                    (isinstance(v, float) and math.isnan(v))
            ):
                v = na_value
            set_elt(r_vector, i, cast_value(v))
    return f


_str_populate_r_vector = _populate_r_vector_with_na(na_values.NA_Character)
_bool_populate_r_vector = _populate_r_vector_with_na(na_values.NA_Logical)
_float_populate_r_vector = _populate_r_vector_with_na(na_values.NA_Real)


def _int_populate_r_vector(iterable, r_vector,
                           set_elt,
                           cast_value):
    for i, v in enumerate(iterable):
        if v is None or v is pandas.NA:
            v = math.nan
        set_elt(r_vector, i, cast_value(v))


_PANDASTYPE2RPY2 = {
    datetime.date: DateVector,
    int: functools.partial(
        IntVector.from_iterable,
        populate_func=_int_populate_r_vector
    ),
    pandas.BooleanDtype: functools.partial(
        BoolVector.from_iterable,
        populate_func=_bool_populate_r_vector
    ),
    None: BoolVector,
    bool: BoolVector,
    str: functools.partial(
        StrVector.from_iterable,
        populate_func=_str_populate_r_vector
    ),
    pandas.Float64Dtype: functools.partial(
        FloatVector.from_iterable,
        populate_func=_float_populate_r_vector
    ),
    bytes: (numpy2ri.converter.py2rpy.registry[
        numpy.ndarray
    ])
}


@py2rpy.register(pandas.core.series.Series)
def py2rpy_pandasseries(obj):
    if obj.dtype.name == 'O':
        warnings.warn('Element "%s" is of dtype "O" and converted '
                      'to R vector of strings.' % obj.name)
        res = StrVector(obj)
    elif obj.dtype.name == 'category':
        res = py2rpy_categorical(obj.cat)
        res = FactorVector(res)
    elif is_datetime64_any_dtype(obj.dtype):
        # time series
        if obj.dt.tz:
            if obj.dt.tz is datetime.timezone.utc:
                tzname = 'UTC'
            else:
                tzname = obj.dt.tz.zone
        else:
            tzname = ''
        d = [IntVector([x.year for x in obj]),
             IntVector([x.month for x in obj]),
             IntVector([x.day for x in obj]),
             IntVector([x.hour for x in obj]),
             IntVector([x.minute for x in obj]),
             FloatSexpVector([x.second + x.microsecond * 1e-6 for x in obj])]
        res = ISOdatetime(*d, tz=StrSexpVector([tzname]))
        # TODO: can the POSIXct be created from the POSIXct constructor ?
        # (is '<M8[ns]' mapping to Python datetime.datetime ?)
        res = POSIXct(res)
    elif obj.dtype.type is str:
        res = _PANDASTYPE2RPY2[str](obj)
    elif obj.dtype.name in integer_array_types:
        res = _PANDASTYPE2RPY2[int](obj)
        if len(obj.shape) == 1:
            if obj.dtype != dt_O_type:
                # force into an R vector
                res = as_vector(res)
    elif (obj.dtype == dt_O_type):
        homogeneous_type = None
        for x in obj.values:
            if x is None:
                continue
            if homogeneous_type is None:
                homogeneous_type = type(x)
                continue
            if ((type(x) is not homogeneous_type)
                and not
                ((isinstance(x, float) and math.isnan(x))
                 or pandas.isna(x))):
                raise ValueError(
                    'Series can only be of one type, or None '
                    '(and here we have %s and %s). If happening with '
                    'a pandas DataFrame the method infer_objects() '
                    'will normalize data types before conversion.' %
                    (homogeneous_type, type(x)))
        # TODO: Could this be merged with obj.type.name == 'O' case above ?
        res = _PANDASTYPE2RPY2[homogeneous_type](obj)
    elif type(obj.dtype) in (pandas.Float64Dtype, pandas.BooleanDtype):
        res = _PANDASTYPE2RPY2[type(obj.dtype)](obj)
    else:
        # converted as a numpy array
        func = numpy2ri.converter.py2rpy.registry[numpy.ndarray]
        # current conversion as performed by numpy

        res = func(obj.values)
        if len(obj.shape) == 1:
            if (obj.dtype != dt_O_type):
                # force into an R vector
                res = as_vector(res)

    # "index" is equivalent to "names" in R
    if obj.ndim == 1:
        res.do_slot_assign('names',
                           StrVector(tuple(str(x) for x in obj.index)))
    else:
        res.do_slot_assign('dimnames',
                           SexpVector(conversion.converter_ctx
                                      .get().py2rpy(obj.index)))
    return res


@rpy2py.register(SexpVector)
def ri2py_vector(obj):
    res = numpy2ri.rpy2py(obj)
    return res


@rpy2py.register(FloatSexpVector)
def rpy2py_floatvector(obj):
    if POSIXct.isrinstance(obj):
        return rpy2py(POSIXct(obj))
    else:
        return numpy2ri.rpy2py(obj)


@rpy2py.register(POSIXct)
def rpy2py_posixct(obj):
    return pandas.to_datetime(tuple(obj.iter_localized_datetime()),
                              errors='coerce')


def _records_to_columns(obj):
    columns = OrderedDict()
    obj_ri = ListSexpVector(obj)
    # First pass to get the column names.
    for i, record in enumerate(obj_ri):
        checknames = set()
        for name in record.names:
            if name in checknames:
                raise ValueError(
                    f'The record {i} has "{name}" duplicated.'
                )
            checknames.add(name)
            if name not in columns:
                columns[name] = []
    columnnames = set(columns.keys())
    # Second pass to fill the columns.
    for i, record in enumerate(obj_ri):
        checknames = set()
        for name, value in zip(record.names, record):
            checknames.add(name)
            if hasattr(value, '__len__'):
                if len(value) != 1:
                    raise ValueError(
                        f'The value for "{name}" record {i} is not a scalar. '
                        f'It has {len(value)} elements.'
                    )
                else:
                    value = value[0]
            columns[name].append(value)
        # Set to NA/None missing column values in the record.
        for name in columnnames-checknames:
            columns[name].append(None)
    return columns


def _flatten_dataframe(obj, colnames_lst):
    """Make each element in a list of columns or group of
    columns iterable.

    This is an helper function to make the "flattening" of columns
    in an R data frame easier as each item in the top-level iterable
    can be a column or list or records (themselves each with an
    arbitrary number of columns).

    Args:
    - colnames_list: an *empty* list that will be populated with
    column names.
    """
    for i, n in enumerate(obj.colnames):
        col = obj[i]
        if isinstance(col, ListSexpVector):
            _ = _records_to_columns(col)
            colnames_lst.extend((n, subn) for subn in _.keys())
            for subcol in _.values():
                yield subcol
        else:
            colnames_lst.append(n)
            yield col


@rpy2py.register(DataFrame)
def rpy2py_dataframe(obj):
    rpy2py = conversion.get_conversion().rpy2py
    colnames_lst = []
    od = OrderedDict(
        (i, rpy2py(col) if isinstance(col, rinterface.SexpVector) else col)
        for i, col in enumerate(_flatten_dataframe(obj, colnames_lst))
    )

    res = pandas.DataFrame.from_dict(od)
    res.columns = tuple('.'.join(_) if isinstance(_, list) else _ for _ in colnames_lst)
    res.index = obj.rownames
    return res


def _to_pandas_factor(obj):
    codes = [x-1 if x > 0 else -1 for x in numpy.array(obj)]
    res = pandas.Categorical.from_codes(
        codes,
        categories=list(obj.do_slot('levels')),
        ordered='ordered' in obj.rclass
    )
    return res


converter._rpy2py_nc_map.update(
    {
        rinterface.IntSexpVector: conversion.NameClassMap(
            numpy2ri.rpy2py,
            {'factor': _to_pandas_factor}
        ),
        rinterface.ListSexpVector: conversion.NameClassMap(
            numpy2ri.rpy2py_list,
            {'data.frame': lambda obj: rpy2py(DataFrame(obj))}
        )
    }
)


def activate():
    warnings.warn('The global conversion available with activate() '
                  'is deprecated and will be removed in the next '
                  'major release. Use a local converter.',
                  category=DeprecationWarning)
    global original_converter
    # If module is already activated, there is nothing to do.
    if original_converter is not None:
        return

    original_converter = conversion.Converter(
        'snapshot before pandas conversion',
        template=conversion.get_conversion())
    numpy2ri.activate()
    new_converter = conversion.Converter('snapshot before pandas conversion',
                                         template=conversion.get_conversion())
    numpy2ri.deactivate()

    for k, v in py2rpy.registry.items():
        if k is object:
            continue
        new_converter.py2rpy.register(k, v)

    for k, v in rpy2py.registry.items():
        if k is object:
            continue
        new_converter.rpy2py.register(k, v)

    conversion.set_conversion(new_converter)


def deactivate():
    global original_converter

    # If module has never been activated or already deactivated,
    # there is nothing to do
    if original_converter is None:
        return

    conversion.set_conversion(original_converter)
    original_converter = None
