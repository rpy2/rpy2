import rpy2.robjects as ro
import rpy2.robjects.conversion as conversion
import rpy2.rinterface as rinterface
import rpy2.rlike.container as rlc
from rpy2.rinterface import (Sexp,
                             StrSexpVector, ByteSexpVector,
                             RTYPES)
import numpy  # type: ignore

# TODO: move this to rinterface.
RINT_SIZE = 32

original_converter = None

# The possible kind codes are listed at
#   http://numpy.scipy.org/array_interface.shtml
_kinds = {
    # "t" -> not really supported by numpy
    'b': ro.vectors.BoolVector,
    'i': ro.vectors.IntVector,
    # "u" -> special-cased below
    'f': ro.vectors.FloatVector,
    'c': ro.vectors.ComplexVector,
    # "O" -> special-cased below
    'S': ro.vectors.ByteVector,
    'U': ro.vectors.StrVector,
    # "V" -> special-cased below
    # TODO: datetime64 ?
    # "datetime64":
    }


_vectortypes = set(
    (
        # TODO: CHARSXP is an fact a scalar.
        RTYPES.CHARSXP,
        RTYPES.LGLSXP,
        RTYPES.INTSXP,
        RTYPES.REALSXP,
        RTYPES.CPLXSXP,
        RTYPES.STRSXP
    )
)

converter = conversion.Converter('original numpy conversion')
py2rpy = converter.py2rpy
rpy2py = converter.rpy2py


def numpy_O_py2rpy(o):
    if all(isinstance(x, str) for x in o):
        res = StrSexpVector(o)
    elif all(isinstance(x, bytes) for x in o):
        res = ByteSexpVector(o)
    else:
        res = conversion.get_conversion().py2rpy(list(o))
    return res


def _numpyarray_to_r(a, func):
    # "F" means "use column-major order"
    vec = func(numpy.ravel(a, order='F'))
    # TODO: no dimnames ?
    # TODO: optimize what is below needed/possible ?
    #  (other ways to create R arrays ?)
    dim = ro.vectors.IntVector(a.shape)
    res = rinterface.baseenv['array'](vec, dim=dim)
    return res


def unsignednumpyint_to_rint(intarray):
    """Convert a numpy array of unsigned integers to an R array."""
    if intarray.itemsize >= (RINT_SIZE / 8):
        raise ValueError(
            'Cannot convert numpy array of {numpy_type!s} '
            '(R integers are signed {RINT_SIZE}-bit integers).'
            .format(numpy_type=intarray.dtype.type,
                    RINT_SIZE=RINT_SIZE)
        )
    else:
        res = _numpyarray_to_r(intarray, _kinds['i'])
    return res


@py2rpy.register(numpy.ndarray)
def numpy2rpy(o):
    """ Augmented conversion function, converting numpy arrays into
    rpy2.rinterface-level R structures. """
    if not o.dtype.isnative:
        raise ValueError('Cannot pass numpy arrays with non-native '
                         'byte orders at the moment.')

    # Most types map onto R arrays:
    if o.dtype.kind in _kinds:
        res = _numpyarray_to_r(o, _kinds[o.dtype.kind])
    # R does not support unsigned types:
    elif o.dtype.kind == 'u':
        res = unsignednumpyint_to_rint(o)
    # Array-of-PyObject is treated like a Python list:
    elif o.dtype.kind == 'O':
        res = numpy_O_py2rpy(o)
    # Record arrays map onto R data frames:
    elif o.dtype.kind == 'V':
        if o.dtype.names is None:
            raise ValueError('Nothing can be done for this numpy array '
                             'type "%s" at the moment.' % (o.dtype,))
        df_args = []
        cv = conversion.get_conversion()
        for field_name in o.dtype.names:
            df_args.append((field_name,
                            cv.py2rpy(o[field_name])))
        res = ro.baseenv["data.frame"].rcall(tuple(df_args))
    # It should be impossible to get here:
    else:
        raise ValueError('Unknown numpy array type "%s".' % str(o.dtype))
    return res


@py2rpy.register(numpy.integer)
def npint_py2rpy(obj):
    return rinterface.IntSexpVector([obj, ])


@py2rpy.register(numpy.floating)
def npfloat_py2rpy(obj):
    return rinterface.FloatSexpVector([obj, ])


@py2rpy.register(object)
def nonnumpy2rpy(obj):
    # allow array-like objects to also function with this module.
    if not isinstance(obj, numpy.ndarray) and hasattr(obj, '__array__'):
        obj = obj.__array__()
        return ro.default_converter.py2rpy(obj)
    elif original_converter is None:
        # This means that the conversion module was not "activated".
        # For now, go with the default_converter.
        # TODO: the conversion system needs an overhaul badly.
        return ro.default_converter.py2rpy(obj)
    else:
        # The conversion module was "activated"
        return original_converter.py2rpy(obj)


# TODO: deprecate.
@py2rpy.register(rlc.OrdDict)
def orddict_py2rpy(obj):
    rlist = ro.vectors.ListVector.from_length(len(obj))
    rlist.names = ro.vectors.StrVector(tuple(obj.keys()))
    with conversion.get_conversion().context() as cv:
        for i, v in enumerate(obj.values()):
            rlist[i] = cv.py2rpy(v)
    return rlist


@py2rpy.register(rlc.NamedList)
def namedlist_py2rpy(obj: rlc.NamedList):
    rlist = ro.vectors.ListVector.from_length(len(obj))
    rlist.names = ro.vectors.StrVector(tuple(obj.names()))
    with conversion.get_conversion().context() as cv:
        for i, v in enumerate(obj.values()):
            rlist[i] = cv.py2rpy(v)
    return rlist


# TODO: delete ?
# @py2ro.register(numpy.ndarray)
# def numpy2ro(obj):
#     res = numpy2ri(obj)
#     return ro.vectors.rtypeof2rotype[res.typeof](res)

def _factor_to_numpy_string_array(obj):
    levels = obj.do_slot('levels')
    res = numpy.array(
        tuple(
            None if x is rinterface.NA_Character
            else levels[x-1] for x in obj
        )
    )
    return res


def rpy2py_data_frame(obj):
    # TODO: R "factor" vectors will not convert well by default
    # (will become integers), so we build a temporary list o2
    # with the factors as strings. This fix might good to have
    # as a default.
    o2 = list()
    # An added complication is that the conversion defined
    # in this module will make __getitem__ at the robjects
    # level return numpy arrays
    with conversion.get_conversion().context() as cv:
        for column in rinterface.ListSexpVector(obj):
            if 'factor' in column.rclass:
                levels = column.do_slot('levels')
                column = tuple(
                    None if x is rinterface.NA_Integer
                    else levels[x-1] for x in column
                )
            o2.append(cv.rpy2py(column))
    names = obj.do_slot('names')
    if names == rinterface.NULL:
        res = numpy.rec.fromarrays(o2)
    else:
        res = numpy.rec.fromarrays(o2, names=tuple(names))
    return res


def rpy2py_list(obj: rinterface.ListSexpVector):
    # not a data.frame, yet is it still possible to convert it
    if not isinstance(obj, ro.vectors.ListVector):
        obj = ro.vectors.ListVector(obj)
    res = rlc.NamedList.from_items(obj.items())
    return res


@rpy2py.register(rinterface.FloatSexpVector)
def rpy2py_floatvector(obj):
    return numpy.array(obj)


@rpy2py.register(rinterface.CharSexp)
def rpy2py_charvector(obj):
    if obj == rinterface.NA_Character:
        return None
    else:
        return obj


@rpy2py.register(rinterface.StrSexpVector)
def rpy2py_strvector(obj):
    res = numpy.array(obj)
    res[res == rinterface.NA_Character] = None
    return res


@rpy2py.register(Sexp)
def rpy2py_sexp(obj):
    if (obj.typeof in _vectortypes) and (obj.typeof != RTYPES.VECSXP):
        res = numpy.array(obj)
    else:
        res = ro.default_converter.rpy2py(obj)
    return res


converter._rpy2py_nc_map.update(
    {
        rinterface.IntSexpVector: conversion.NameClassMap(
            numpy.array,
            {'factor': _factor_to_numpy_string_array}
        ),
        rinterface.ListSexpVector: conversion.NameClassMap(
            rpy2py_list,
            {'data.frame': rpy2py_data_frame}
        )
    }
)


_DEPRECATION_MSG = """
The activate and deactivate are deprecated. To set a conversion
context check the docstring for rpy2.robjects.conversion.Converter.context.
"""


def activate():
    raise DeprecationWarning(_DEPRECATION_MSG)


def deactivate():
    raise DeprecationWarning(_DEPRECATION_MSG)
