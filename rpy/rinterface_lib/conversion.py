"""Conversion between Python objects, C objects, and R objects."""

# TODO: rename the module with a prefix _ to indicate that this should
#   not be used outside of rpy2's own code

from _rinterface_cffi import ffi
from . import openrlib
from . import _rinterface_capi as _rinterface

_R_RPY2_MAP = {}
_R_RPY2_DEFAULT_MAP = None

_PY_RPY2_MAP = {}


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
    # TODO: test value is not too large for R's ints
    s = rlib.Rf_protect(rlib.Rf_allocVector(rlib.INTSXP, 1))
    openrlib.SET_INTEGER_ELT(s, 0, val)
    rlib.Rf_unprotect(1)
    return s


def _bool_to_sexp(val: bool):
    # TODO: test value is not too large for R's ints
    rlib = openrlib.rlib
    s = rlib.Rf_protect(rlib.Rf_allocVector(rlib.LGLSXP, 1))
    openrlib.SET_LOGICAL_ELT(s, 0, int(val))
    rlib.Rf_unprotect(1)
    return s


def _float_to_sexp(val: float):
    rlib = openrlib.rlib
    s = rlib.Rf_protect(rlib.Rf_allocVector(rlib.REALSXP, 1))
    openrlib.SET_REAL_ELT(s, 0, val)
    rlib.Rf_unprotect(1)
    return s


def _complex_to_sexp(val: complex):
    rlib = openrlib.rlib
    s = rlib.Rf_protect(rlib.Rf_allocVector(rlib.CPLXSXP, 1))
    openrlib.SET_COMPLEX_ELT(
        s, 0,
        val
    )
    rlib.Rf_unprotect(1)
    return s


# {
#     'ASCII'
#     'latin-1': rlib.cetype_t.CE_LATIN1,
#     'utf-8': rlib.cetype_t.CE_UTF8,
# }
_CE_UTF8 = 2


def _str_to_cchar(s, encoding: str = 'utf-8'):
    # TODO: use isStrinb and installTrChar
    b = s.encode(encoding)
    return ffi.new('char[]', b)


def _cchar_to_str(c, encoding: str = 'utf-8'):
    # TODO: use isStrinb and installTrChar
    s = ffi.string(c).decode(encoding)
    return s


def _cchar_to_str_with_maxlen(c, maxlen: int):
    # TODO: use isStrinb and installTrChar
    s = ffi.string(c, maxlen).decode('utf-8')
    return s


def _str_to_charsxp(val: str):
    rlib = openrlib.rlib
    if val is None:
        s = rlib.R_NaString
    else:
        cchar = _str_to_cchar(val)
        s = rlib.Rf_mkCharCE(cchar, _CE_UTF8)
    return s


def _str_to_sexp(val: str):
    rlib = openrlib.rlib
    s = rlib.Rf_protect(rlib.Rf_allocVector(rlib.STRSXP, 1))
    charval = _str_to_charsxp(val)
    rlib.SET_STRING_ELT(s, 0, charval)
    rlib.Rf_unprotect(1)
    return s


def _str_to_symsxp(val: str):
    rlib = openrlib.rlib
    cchar = _str_to_cchar(val)
    s = rlib.Rf_install(cchar)
    return s


_PY_R_MAP = {}


# TODO: Do special values such as NAs need to be cast into a SEXP when
#   a scalar ?
def _get_cdata(obj):
    cast = _PY_R_MAP.get(type(obj))
    if cast is False:
        cdata = obj
    elif cast is None:
        try:
            cdata = obj.__sexp__._cdata
        except AttributeError:
            raise ValueError('Not an rpy2 R object and unable '
                             'to cast it into one: %s' % repr(obj))
    else:
        cdata = cast(obj)
    return cdata
