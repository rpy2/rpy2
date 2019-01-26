import platform
import rpy2.situation
from _rinterface_cffi import ffi


# TODO: Separate the functions in the module from the side-effect of
# finding R_HOME and opening the shared library.
R_HOME = rpy2.situation.get_r_home()


def _dlopen_rlib(r_home: str):
    """Open R's shared C library."""
    if r_home is None:
        raise ValueError('r_home is None. '
                         'Try python -m rpy2.situation')
    lib_path = rpy2.situation.get_rlib_path(r_home, platform.system())
    rlib = ffi.dlopen(lib_path)
    return rlib


rlib = _dlopen_rlib(R_HOME)


# R macros and functions
def _get_symbol_or_fallback(symbol: str, fallback):
    """Get a cffi object from rlib, or the fallback if missing."""
    try:
        res = getattr(rlib, symbol)
    except ffi.error:
        res = fallback
    return res


def _get_dataptr_fallback(vec):
    # '(((SEXPREC_ALIGN *) (x)) + 1)'
    ptr = ffi.cast('SEXPREC_ALIGN *', vec)
    ptr += 1
    return ffi.cast('void *', ptr)


DATAPTR = _get_symbol_or_fallback('DATAPTR',
                                  _get_dataptr_fallback)


def _LOGICAL(x):
    return ffi.cast('int *', DATAPTR(x))


def _INTEGER(x):
    return ffi.cast('int *', DATAPTR(x))


def _RAW(x):
    return ffi.cast('Rbyte *', DATAPTR(x))


def _REAL(robj):
    return ffi.cast('double *', DATAPTR(robj))


def _COMPLEX(robj):
    return ffi.cast('Rcomplex *', DATAPTR(robj))


def _get_integer_elt_fallback(vec, i: int):
    return _INTEGER(vec)[i]


INTEGER_ELT = _get_symbol_or_fallback('INTEGER_ELT',
                                      _get_integer_elt_fallback)


def _set_integer_elt_fallback(vec, i: int, value):
    _INTEGER(vec)[i] = value


SET_INTEGER_ELT = _get_symbol_or_fallback('SET_INTEGER_ELT',
                                          _set_integer_elt_fallback)


def _get_logical_elt_fallback(vec, i: int):
    return _LOGICAL(vec)[i]


LOGICAL_ELT = _get_symbol_or_fallback('LOGICAL_ELT',
                                      _get_logical_elt_fallback)


def _set_logical_elt_fallback(vec, i: int, value):
    _LOGICAL(vec)[i] = value


SET_LOGICAL_ELT = _get_symbol_or_fallback('SET_LOGICAL_ELT',
                                          _set_logical_elt_fallback)


def _get_real_elt_fallback(vec, i: int):
    return _REAL(vec)[i]


REAL_ELT = _get_symbol_or_fallback('REAL_ELT',
                                   _get_real_elt_fallback)


def _set_real_elt_fallback(vec, i: int, value):
    _REAL(vec)[i] = value


SET_REAL_ELT = _get_symbol_or_fallback('SET_REAL_ELT',
                                       _set_real_elt_fallback)


# TODO: still useful or is it in the C API ?
def _VECTOR_ELT(robj, i):
    return ffi.cast('SEXP *', DATAPTR(robj))[i]


def _STRING_PTR(robj):
    return ffi.cast('SEXP *', DATAPTR(robj))


def _VECTOR_PTR(robj):
    return ffi.cast('SEXP *', DATAPTR(robj))


def _STRING_VALUE(robj):
    return rlib.R_CHAR(rlib.Rf_asChar(robj))
