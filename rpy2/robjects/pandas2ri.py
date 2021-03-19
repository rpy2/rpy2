"""This module handles the conversion of data structures
between R objects handled by rpy2 and pandas objects."""

import rpy2.robjects.conversion as conversion
import rpy2.rinterface as rinterface
from rpy2.rinterface_lib import na_values
from rpy2.rinterface import (IntSexpVector,
                             ListSexpVector,
                             Sexp,
                             SexpVector,
                             StrSexpVector)
import datetime
import functools
import math
import numpy
import pandas
import pandas.core.series
from pandas.core.frame import DataFrame as PandasDataFrame
from pandas.core.dtypes.api import is_datetime64_any_dtype
import warnings

from collections import OrderedDict
from rpy2.robjects.vectors import (BoolVector,
                                   DataFrame,
                                   DateVector,
                                   FactorVector,
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
    od = OrderedDict()
    for name, values in obj.iteritems():
        try:
            od[name] = conversion.py2rpy(values)
        except Exception as e:
            warnings.warn('Error while trying to convert '
                          'the column "%s". Fall back to string conversion. '
                          'The error is: %s'
                          % (name, str(e)))
            od[name] = StrVector(values)

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


def py2rpy_categoryseries(obj):
    for c in obj.cat.categories:
        if not isinstance(c, str):
            raise ValueError('Converting pandas "Category" series to '
                             'R factor is only possible when categories '
                             'are strings.')
    res = IntSexpVector(list(rinterface.NA_Integer if x == -1 else x+1
                             for x in obj.cat.codes))
    res.do_slot_assign('levels', StrSexpVector(obj.cat.categories))
    if obj.cat.ordered:
        res.rclass = StrSexpVector(('ordered', 'factor'))
    else:
        res.rclass = StrSexpVector(('factor',))
    return res


def _str_populate_r_vector(iterable, r_vector,
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
            v = na_values.NA_Character
        set_elt(r_vector, i, cast_value(v))


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
    bool: BoolVector,
    None: BoolVector,
    str: functools.partial(
        StrVector.from_iterable,
        populate_func=_str_populate_r_vector
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
        res = py2rpy_categoryseries(obj)
        res = FactorVector(res)
    elif is_datetime64_any_dtype(obj.dtype):
        # time series
        tzname = obj.dt.tz.zone if obj.dt.tz else ''
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
    elif obj.dtype.type == str:
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
                raise ValueError('Series can only be of one type, or None '
                                 '(and here we have %s and %s).' %
                                 (homogeneous_type, type(x)))
        # TODO: Could this be merged with obj.type.name == 'O' case above ?
        res = _PANDASTYPE2RPY2[homogeneous_type](obj)
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
                           SexpVector(conversion.py2rpy(obj.index)))
    return res


@rpy2py.register(SexpVector)
def ri2py_vector(obj):
    res = numpy2ri.rpy2py(obj)
    return res


@rpy2py.register(IntSexpVector)
def rpy2py_intvector(obj):
    # special case for factors
    if 'factor' in obj.rclass:
        codes = [x-1 if x > 0 else -1 for x in numpy.array(obj)]
        res = pandas.Categorical.from_codes(
            codes,
            categories=list(obj.do_slot('levels')),
            ordered='ordered' in obj.rclass
        )
    else:
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


@rpy2py.register(ListSexpVector)
def rpy2py_listvector(obj):
    if 'data.frame' in obj.rclass:
        res = rpy2py(DataFrame(obj))
    else:
        res = numpy2ri.rpy2py(obj)
    return res


@rpy2py.register(DataFrame)
def rpy2py_dataframe(obj):
    items = OrderedDict((k, rpy2py(v) if isinstance(v, Sexp) else v)
                        for k, v in obj.items())
    res = PandasDataFrame.from_dict(items)
    res.index = obj.rownames
    return res


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
        template=conversion.converter)
    numpy2ri.activate()
    new_converter = conversion.Converter('snapshot before pandas conversion',
                                         template=conversion.converter)
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
