"""This module handles the conversion of data structures
between R objects handled by rpy2 and pandas objects."""

from datetime import datetime
import rpy2.robjects.conversion as conversion
import rpy2.rinterface as rinterface
from rpy2.rinterface import (IntSexpVector,
                             ListSexpVector,
                             Sexp,
                             SexpVector,
                             StrSexpVector)

from pandas.core.frame import DataFrame as PandasDataFrame
from pandas.core.series import Series as PandasSeries
from pandas.core.index import Index as PandasIndex
from pandas.core.dtypes.api import is_datetime64_any_dtype
import pandas
import numpy
import pytz
import tzlocal
import warnings

from collections import OrderedDict
from rpy2.robjects.vectors import (BoolVector,
                                   DataFrame,
                                   FactorVector,
                                   FloatSexpVector,
                                   StrVector,
                                   IntVector,
                                   POSIXct)

# pandas is requiring numpy. We add the numpy conversion will be
# activate in the function activate() below.
import rpy2.robjects.numpy2ri as numpy2ri

original_converter = None

ISOdatetime = rinterface.baseenv['ISOdatetime']
as_vector = rinterface.baseenv['as.vector']

converter = conversion.Converter('original pandas conversion')
py2rpy = converter.py2rpy
rpy2py = converter.rpy2py


# numpy types for Pandas columns that require (even more) special handling
dt_O_type = numpy.dtype('O')

default_timezone = None


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


@py2rpy.register(PandasIndex)
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


@py2rpy.register(PandasSeries)
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
    elif (obj.dtype == dt_O_type):
        homogeneous_type = None
        for x in obj.values:
            if x is None:
                continue
            if homogeneous_type is None:
                homogeneous_type = type(x)
                continue
            if type(x) is not homogeneous_type:
                raise ValueError('Series can only be of one type, or None.')
        # TODO: Could this be merged with obj.type.name == 'O' case above ?
        res = {
            int: IntVector,
            bool: BoolVector,
            None: BoolVector,
            str: StrVector,
            bytes: numpy2ri.converter.py2rpy.registry[
                numpy.ndarray
            ]
        }[homogeneous_type](obj)
    else:
        # converted as a numpy array
        func = numpy2ri.converter.py2rpy.registry[numpy.ndarray]
        # current conversion as performed by numpy

        res = func(obj)
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


def get_timezone():
    """ Return the system's timezone settings. """
    if default_timezone:
        timezone = default_timezone
    else:
        timezone = tzlocal.get_localzone()
    return timezone


@rpy2py.register(FloatSexpVector)
def rpy2py_floatvector(obj):
    # special case for POSIXct date objects
    if 'POSIXct' in obj.rclass:
        try:
            tzone_name = obj.do_slot('tzone')[0]
        except LookupError:
            warnings.warn('R object inheriting from "POSIXct" but without '
                          'attribute "tzone".')
            tzone_name = ''
        if tzone_name == '':
            # R is implicitly using the local timezone, while Python
            # time libraries will assume UTC.
            tzone = get_timezone()
        else:
            tzone = pytz.timezone(tzone_name)
        foo = (tzone.localize(datetime.fromtimestamp(x)) for x in obj)
        res = pandas.to_datetime(tuple(foo))
    else:
        res = numpy2ri.rpy2py(obj)
    return res


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
