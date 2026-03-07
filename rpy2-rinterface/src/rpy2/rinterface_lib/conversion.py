"""Mapping between Python objects, C objects, and R objects."""

# TODO: rename the module with a prefix _ to indicate that this should
#   not be used outside of rpy2's own code

from typing import Callable
from typing import Dict
from typing import Literal
from typing import Optional
from typing import Type
from typing import Union
from rpy2.rinterface_lib import openrlib
from rpy2.rinterface_lib import _rinterface_capi as _rinterface

ffi = openrlib.ffi

_R_RPY2_MAP = {}  # type: Dict[int, Type]


class DummyMissingRpy2Map(object):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError('The default object mapper class is no set.')


_R_RPY2_DEFAULT_MAP: Type[
    Union[DummyMissingRpy2Map, '_rinterface.SupportsSEXP']
] = DummyMissingRpy2Map

# TODO: shouldn't the second type strictly inherit from an rpy2
# R object ?
_PY_RPY2_MAP: Dict[Type, Callable] = {}


def _cdata_to_rinterface(cdata):
    scaps = _rinterface.SexpCapsule(cdata)
    t = cdata.sxpinfo.type
    if t in _R_RPY2_MAP:
        cls = _R_RPY2_MAP[t]
    else:
        cls = _R_RPY2_DEFAULT_MAP
    return cls(scaps)


def _cdata_res_to_rinterface(function):
    def _(*args, **kwargs):
        cdata = function(*args, **kwargs)
        # TODO: test cdata is of the expected CType
        return _cdata_to_rinterface(cdata)
    return _


def _sexpcapsule_to_rinterface(scaps: '_rinterface.SexpCapsule'):
    cls = _R_RPY2_MAP.get(scaps.typeof, _R_RPY2_DEFAULT_MAP)
    return cls(scaps)


# TODO: The name of the function is misleading, I think. Consider changing it.
def _python_to_cdata(obj):
    t = type(obj)
    if t in _PY_RPY2_MAP:
        cls = _PY_RPY2_MAP[t]
    else:
        raise ValueError(obj)
        # cls = _PY_RPY2_DEFAULT_MAP
    cdata = cls(obj)
    return cdata


# TODO: can scalars in R's C API be used ?
def _int_to_sexp(val: int):
    rlib = openrlib.rlib
    # TODO: _rinterface._MAX_INT is determined empirically.
    if val > _rinterface._MAX_INT:
        raise ValueError(
            f'The Python integer {val} is larger than {_rinterface._MAX_INT} ('
            'R\'s largest possible integer).'
        )
    try:
        openrlib.lock.acquire()
        s = rlib.Rf_protect(rlib.Rf_allocVector(rlib.INTSXP, 1))
        openrlib.SET_INTEGER_ELT(s, 0, val)
        rlib.Rf_unprotect(1)
    finally:
        openrlib.lock.release()
    return s


def _bool_to_sexp(val: bool):
    # TODO: test value is not too large for R's ints
    rlib = openrlib.rlib
    try:
        openrlib.lock.acquire()
        s = rlib.Rf_protect(rlib.Rf_allocVector(rlib.LGLSXP, 1))
        openrlib.SET_LOGICAL_ELT(s, 0, int(val))
        rlib.Rf_unprotect(1)
    finally:
        openrlib.lock.release()
    return s


def _float_to_sexp(val: float):
    rlib = openrlib.rlib
    s = rlib.Rf_protect(rlib.Rf_allocVector(rlib.REALSXP, 1))
    openrlib.SET_REAL_ELT(s, 0, val)
    rlib.Rf_unprotect(1)
    return s


def _complex_to_sexp(val: complex):
    rlib = openrlib.rlib
    try:
        openrlib.lock.acquire()
        s = rlib.Rf_protect(rlib.Rf_allocVector(rlib.CPLXSXP, 1))
        try:
            openrlib.SET_COMPLEX_ELT(
                s, 0,
                val
            )
        finally:
            rlib.Rf_unprotect(1)
    finally:
        openrlib.lock.release()
    return s


# Default encoding for converting R string back to Python
# as defined in R_API.h. The Python Enum
# rinterface_lib.sexp.CETYPE lists the values.
# Otherwise the C definitions are:
#   CE_NATIVE = 0,
#   CE_UTF8   = 1,
#   CE_LATIN1 = 2,
#   CE_BYTES  = 3,
#   CE_SYMBOL = 5,
#   CE_ANY    = 99
# TODO: make _ENC_R_TYPE an explicit type definition as soon as Python >= 3.12.
_ENC_R_TYPE = Literal[0, 1, 2, 3, 5, 99]

# Default encoding for converting strings between R and Python.
_ENC_PY: str = 'utf-8'
_ENC_R: _ENC_R_TYPE = openrlib.rlib.CE_UTF8


def _str_to_cchar(s: str, encoding: str):
    # TODO: use isString and installTrChar
    b = s.encode(encoding)
    return ffi.new('char[]', b)


def _cchar_to_str(c, encoding: str) -> str:
    # TODO: use isString and installTrChar
    s = ffi.string(c).decode(encoding)
    return s


def _cchar_to_str_with_maxlen(c, maxlen: int, encoding: str) -> str:
    # TODO: use isString and installTrChar
    s = ffi.string(c, maxlen).decode(encoding)
    return s


def _utf8_rchar_to_str(rchar) -> str:
    # WARNING: cchar is allocated from an R-managed
    # memory allocation system. We copy it quasi-immediately
    # to create the Python str returned but it is unclear whether
    # the memory is ever freed.
    cchar = openrlib.rlib.Rf_translateCharUTF8(rchar)
    return ffi.string(cchar).decode('utf-8')


# TODO: rename to `_charsxp_to_str` for consistency with `_str_to_charsxp`.
def _rchar_to_str(rchar, encoding: str) -> str:
    """Convert a R string scalar to a Python string.

    This function is not thread safe!
    :param:rchar: a cffi pointer to a C-level `CHARSXP`.
    :param:encoding: This is used to create the Python string from the `char *`
    returned by R's `Rf_translateChar`.
    :return: A Python string."""
    # WARNING: cchar is allocated from an R-managed
    # memory allocation system. We copy it quasi-immediately
    # to create the Python str returned but it is unclear whether
    # the memory is ever freed.
    if encoding == 'utf-8':
        return _utf8_rchar_to_str(rchar)
    cchar = openrlib.rlib.Rf_translateChar(rchar)
    return ffi.string(cchar).decode(encoding)


def _utf8_str_to_charsxp(val: Optional[str]):
    """Convert a Python string to an R string scalar.

    This function is not thread safe!"""
    if val is None:
        s = openrlib.rlib.R_NaString
    else:
        cchar = _str_to_cchar(val, 'utf-8')
        s = openrlib.rlib.Rf_mkCharCE(cchar, openrlib.rlib.CE_UTF8)
    return s


def _str_to_charsxp(
        val: Optional[str],
        py_encoding: Optional[str] = None,
        r_encoding: Optional[_ENC_R_TYPE] = None
):
    """Convert a Python string to a R string scalar.

    This function is not thread safe!
    :param:val: A Python string or a None. If the latter, an R `R_NaString` is returned.
    :param:py_encoding: This is used to create the `char *` from the Python string. The
    value for this parameter must be compatible with the value for parameter `r_encoding`.
    :param:r_encoding: This is used to create the R string scalar from the `char *`. The
    value for this parameter must be compatible with the value for parameter `r_encoding`.
    :return: A cffi pointer to a C-level `CHARSXP`."""

    if val is None:
        s = openrlib.rlib.R_NaString
    else:
        if py_encoding is None:
            py_encoding = _ENC_PY
        if r_encoding is None:
            r_encoding = _ENC_R
        cchar = _str_to_cchar(val, py_encoding)
        s = openrlib.rlib.Rf_mkCharCE(cchar, r_encoding)
    return s


def _str_to_sexp(
        obj: str,
        py_encoding: Optional[str] = None,
        r_encoding: Optional[_ENC_R_TYPE] = None
):
    """This function is not thread safe!"""
    if py_encoding is None:
        py_encoding = _ENC_PY
    if r_encoding is None:
        r_encoding = _ENC_R
    return openrlib.rlib.Rf_ScalarString(
        openrlib.rlib.Rf_mkCharCE(
            _str_to_cchar(obj, py_encoding),
            r_encoding
        )
    )


def _str_to_symsxp(obj: str, encoding: str):
    """This function is not thread safe!"""
    cchar = _str_to_cchar(obj, encoding)
    s = openrlib.rlib.Rf_install(cchar)
    return s


_PY_R_MAP = {}  # type: Dict[Type, Union[Callable, None, bool]]


# TODO: Do special values such as NAs need to be mapped into a SEXP when
#   a scalar ?
def _get_cdata(obj):
    cls = _PY_R_MAP.get(type(obj))
    if cls is False:
        cdata = obj
    elif cls is None:
        try:
            cdata = obj.__sexp__._cdata
        except AttributeError:
            raise ValueError('Not an rpy2 R object and unable '
                             'to map it to one: %s' % repr(obj))
    else:
        cdata = cls(obj)
    return cdata
