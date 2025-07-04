import logging
import os
import platform
import sys
import threading
import typing
import rpy2.situation
from rpy2.rinterface_lib import ffi_proxy

logger = logging.getLogger(__name__)

cffi_mode_request = rpy2.situation.get_cffi_mode()

# TODO: Separate the functions in the module from the side-effect of
# finding R_HOME and opening the shared library.
R_HOME = rpy2.situation.get_r_home()

if os.name == 'nt':
    if R_HOME is not None:
        try:
            for libpath in rpy2.situation.get_r_flags(R_HOME, '--ldflags')[0].L:
                os.add_dll_directory(libpath)  # type: ignore[attr-defined]
        except rpy2.situation.subprocess.CalledProcessError:
            if platform.machine().lower() == "arm64":
                libpath = os.path.join(R_HOME, "bin", "R.dll")
            elif sys.maxsize > 2**32:
                libpath = os.path.join(R_HOME, "bin", "x64", "R.dll")
            else:
                libpath = os.path.join(R_HOME, "bin", "i386", "R.dll")
            os.add_dll_directory(libpath)  # type: ignore[attr-defined]
    else:
        logging.warn('R_HOME is None.')
else:
    LD_LIBRARY_PATH = (
        rpy2.situation.r_ld_library_path_from_subprocess(R_HOME)
        if R_HOME is not None
        else ''
    )

if cffi_mode_request == rpy2.situation.CFFI_MODE.API:
    import _rinterface_cffi_api as _rinterface_cffi  # type: ignore
    cffi_mode = rpy2.situation.CFFI_MODE.API
elif cffi_mode_request == rpy2.situation.CFFI_MODE.ABI:
    import _rinterface_cffi_abi as _rinterface_cffi  # type: ignore
    cffi_mode = rpy2.situation.CFFI_MODE.ABI
elif cffi_mode_request == rpy2.situation.CFFI_MODE.ANY:
    try:
        if os.name == 'nt':
            raise ImportError('On Windows, cffi mode "ANY" is only "ABI".')
        else:
            import _rinterface_cffi_api as _rinterface_cffi  # type: ignore
            cffi_mode = rpy2.situation.CFFI_MODE.API
    except ImportError as ie_api:
        logger.warning(
            f'Error importing in API mode: {repr(ie_api)}'
        )
        try:
            import _rinterface_cffi_abi as _rinterface_cffi  # type: ignore
            cffi_mode = rpy2.situation.CFFI_MODE.ABI
            logger.warning('Trying to import in ABI mode.')
        except ImportError as ie_abi:
            logger.error(f'Failed to import the API mode with "{ie_api}" '
                         'and unable to import the ABI mode.')
            raise ie_abi
else:
    raise ImportError(
        f'cffi mode requested invalid: {cffi_mode_request}'
    )
ffi = _rinterface_cffi.ffi

lock = threading.Lock()
rlock = threading.RLock()


def _dlopen_rlib(r_home: typing.Optional[str]):
    """Open R's shared C library.

    This is only relevant in ABI mode."""
    if r_home is None:
        raise ValueError('r_home is None. '
                         'Try python -m rpy2.situation')
    lib_path = rpy2.situation.get_rlib_path(r_home, platform.system())
    if lib_path is None:
        raise ValueError('The library path cannot be None.')
    else:
        rlib = ffi.dlopen(lib_path)
    return rlib


if ffi_proxy.get_ffi_mode(_rinterface_cffi) == ffi_proxy.InterfaceType.API:
    rlib = _rinterface_cffi.lib
else:
    rlib = _dlopen_rlib(R_HOME)


# R macros and functions
def _get_symbol_or_fallback(symbol: str, fallback: typing.Any):
    """Get a cffi object from rlib, or the fallback if missing."""
    try:
        res = getattr(rlib, symbol)
    except (ffi.error, AttributeError):
        res = fallback
    return res


DATAPTR = rlib.DATAPTR


def _LOGICAL(x):
    return ffi.cast('int *', DATAPTR(x))


LOGICAL = rlib.LOGICAL


def _INTEGER(x):
    return ffi.cast('int *', DATAPTR(x))


INTEGER = rlib.INTEGER


def _RAW(x):
    return ffi.cast('Rbyte *', DATAPTR(x))


RAW = rlib.RAW


def _REAL(robj):
    return ffi.cast('double *', DATAPTR(robj))


REAL = rlib.REAL


def _COMPLEX(robj):
    return ffi.cast('Rcomplex *', DATAPTR(robj))


COMPLEX = rlib.COMPLEX


def _get_raw_elt_fallback(vec, i: int):
    return RAW(vec)[i]


RAW_ELT = _get_symbol_or_fallback('RAW_ELT',
                                  _get_raw_elt_fallback)


def _get_integer_elt_fallback(vec, i: int):
    return INTEGER(vec)[i]


INTEGER_ELT = _get_symbol_or_fallback('INTEGER_ELT',
                                      _get_integer_elt_fallback)


def _set_integer_elt_fallback(vec, i: int, value: int):
    INTEGER(vec)[i] = value


SET_INTEGER_ELT = _get_symbol_or_fallback('SET_INTEGER_ELT',
                                          _set_integer_elt_fallback)


def _get_logical_elt_fallback(vec, i: int):
    return LOGICAL(vec)[i]


LOGICAL_ELT = _get_symbol_or_fallback('LOGICAL_ELT',
                                      _get_logical_elt_fallback)


def _set_logical_elt_fallback(vec, i: int, value):
    LOGICAL(vec)[i] = value


SET_LOGICAL_ELT = _get_symbol_or_fallback('SET_LOGICAL_ELT',
                                          _set_logical_elt_fallback)


def _get_real_elt_fallback(vec, i: int):
    return REAL(vec)[i]


REAL_ELT = _get_symbol_or_fallback('REAL_ELT',
                                   _get_real_elt_fallback)


def _set_real_elt_fallback(vec, i: int, value: float):
    REAL(vec)[i] = value


SET_REAL_ELT = _get_symbol_or_fallback('SET_REAL_ELT',
                                       _set_real_elt_fallback)


def _get_complex_elt_fallback(vec, i: int):
    return COMPLEX(vec)[i]


COMPLEX_ELT = _get_symbol_or_fallback('COMPLEX_ELT',
                                      _get_complex_elt_fallback)


def SET_COMPLEX_ELT(vec, i: int, value: complex):
    COMPLEX(vec)[i].r = value.real
    COMPLEX(vec)[i].i = value.imag


# TODO: still useful or is it in the C API?
def _VECTOR_ELT(robj, i):
    return ffi.cast('SEXP *', DATAPTR(robj))[i]


def _PAIRLIST_PTR(robj):
    return ffi.cast('SEXP *', DATAPTR(robj))


def _STRING_PTR(robj):
    return ffi.cast('SEXP *', DATAPTR(robj))


def _VECTOR_PTR(robj):
    return ffi.cast('SEXP *', DATAPTR(robj))


def _STRING_VALUE(robj):
    return rlib.R_CHAR(rlib.Rf_asChar(robj))
