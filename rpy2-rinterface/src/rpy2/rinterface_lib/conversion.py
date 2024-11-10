"""Mapping between Python objects, C objects, and R objects."""

# TODO: rename the module with a prefix _ to indicate that this should
#   not be used outside of rpy2's own code

from typing import Callable
from typing import Dict
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
# As defined in R_API.h, possible values are
#   CE_NATIVE = 0,
#   CE_UTF8   = 1,
#   CE_LATIN1 = 2,
#   CE_BYTES  = 3,
#   CE_SYMBOL = 5,
#   CE_ANY    = 99

# Default encoding for converting R strings to Python
_R_ENC_PY = {None: 'ascii'}


def _str_to_cchar(s: str, encoding: str = 'utf-8'):
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


def _str_to_charsxp(val: Optional[str]):
    """This function is not thread safe!"""
    rlib = openrlib.rlib
    if val is None:
        s = rlib.R_NaString
    else:
        cchar = _str_to_cchar(val, encoding='utf-8')
        s = rlib.Rf_mkCharCE(cchar, openrlib.rlib.CE_UTF8)
    return s


def _str_to_sexp(val: str):
    """This function is not thread safe!"""
    rlib = openrlib.rlib
    s = rlib.Rf_protect(rlib.Rf_allocVector(rlib.STRSXP, 1))
    charval = _str_to_charsxp(val)
    rlib.SET_STRING_ELT(s, 0, charval)
    rlib.Rf_unprotect(1)
    return s


def _str_to_symsxp(val: str):
    """This function is not thread safe!"""
    rlib = openrlib.rlib
    cchar = _str_to_cchar(val)
    s = rlib.Rf_install(cchar)
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
