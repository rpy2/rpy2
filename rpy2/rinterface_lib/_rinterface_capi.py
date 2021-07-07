# TODO: make it cffi-buildable with conditional function definition
# (Python if ABI, C if API)
import abc
import enum
import logging
from typing import Tuple
import typing
import warnings
from rpy2.rinterface_lib import ffi_proxy
from rpy2.rinterface_lib import openrlib
from rpy2.rinterface_lib import conversion
from rpy2.rinterface_lib import embedded
from rpy2.rinterface_lib import memorymanagement

from _cffi_backend import FFI  # type: ignore


logger = logging.getLogger(__name__)

ffi = openrlib.ffi

# TODO: How can I reliably get MAX_INT from limits.h ?
_MAX_INT = 2**32-1

_R_PRESERVED = dict()  # type: typing.Dict[int, int]
_PY_PASSENGER = dict()

FFI_MODE = ffi_proxy.get_ffi_mode(openrlib._rinterface_cffi)


def get_rid(cdata: FFI.CData) -> int:
    """Get the identifier for the R object.

    This is intended to be like Python's `id()`, but
    for R objects mapped by rpy2."""
    return int(ffi.cast('uintptr_t', cdata))


def protected_rids() -> Tuple[Tuple[int, int], ...]:
    """Sequence of R IDs protected from collection by rpy2."""
    keys = tuple(_R_PRESERVED.keys())
    res = []
    for k in keys:
        v = _R_PRESERVED.get(k)
        if v:
            res.append((get_rid(k), v))
    return tuple(res)


def is_cdata_sexp(obj: typing.Any) -> bool:
    """Is the object a cffi `CData` object pointing to an R object ?"""
    if (isinstance(obj, FFI.CData) and
            ffi.typeof(obj).cname == 'struct SEXPREC *'):
        return True
    else:
        return False


def _preserve(cdata: FFI.CData) -> int:
    addr = int(ffi.cast('uintptr_t', cdata))
    count = _R_PRESERVED.get(addr, 0)
    if count == 0:
        openrlib.rlib.R_PreserveObject(cdata)
    _R_PRESERVED[addr] = count + 1
    return addr


def _release(cdata: FFI.CData) -> None:
    addr = int(ffi.cast('uintptr_t', cdata))
    count = _R_PRESERVED[addr] - 1
    if count == 0:
        del(_R_PRESERVED[addr])
        openrlib.rlib.R_ReleaseObject(cdata)
    else:
        _R_PRESERVED[addr] = count


@ffi_proxy.callback(ffi_proxy._capsule_finalizer_def,
                    openrlib._rinterface_cffi)
def _capsule_finalizer(cdata: FFI.CData) -> None:
    try:
        openrlib.rlib.R_ClearExternalPtr(cdata)
    except Exception as e:
        warnings.warn('Exception downgraded to warning: %s' % str(e))


# ABI and API modes differs in what is the exact callback object to be
# passed to C code.
if hasattr(openrlib._rinterface_cffi, 'lib'):
    _capsule_finalizer_c = openrlib._rinterface_cffi.lib._capsule_finalizer
else:
    _capsule_finalizer_c = None


class CapsuleBase:

    _cdata: FFI.CData

    @property
    def typeof(self) -> int:
        return _TYPEOF(self._cdata)

    @property
    def rid(self) -> int:
        return get_rid(self._cdata)


class UninitializedRCapsule(CapsuleBase):

    @property
    def _cdata(self):
        raise RuntimeError('The embedded R is not initialized.')

    @property
    def typeof(self) -> int:
        return self._typeof

    def __init__(self, typeof):
        self._typeof = typeof


class UnmanagedSexpCapsule(CapsuleBase):

    __slots__ = ('_cdata', )

    def __init__(self, cdata: FFI.CData):
        assert is_cdata_sexp(cdata)
        self._cdata = cdata


class SexpCapsule(CapsuleBase):

    __slots__ = ('_cdata', )

    def __init__(self, cdata: FFI.CData):
        assert is_cdata_sexp(cdata)
        _preserve(cdata)
        self._cdata = cdata

    def __del__(self):
        try:
            _release(self._cdata)
        except Exception as e:
            # _release can be None while capsules when Python is terminating
            # and R is being shutdown, resulting in a race condition when
            # freeing python objects.
            if _release is None:
                pass
            else:
                raise e


class SexpCapsuleWithPassenger(SexpCapsule):
    __slots__ = ('_cdata', '_passenger')

    def __init__(self, cdata: FFI.CData, passenger, ptr):
        assert is_cdata_sexp(cdata)
        addr = _preserve(cdata)
        _PY_PASSENGER[addr] = passenger
        self._cdata = cdata
        self._passenger = ptr

    def __del__(self):
        addr = get_rid(self._cdata)
        _release(self._cdata)
        if addr not in _PY_PASSENGER:
            del(_PY_PASSENGER[addr])


class SupportsSEXP(object, metaclass=abc.ABCMeta):

    @abc.abstractproperty
    def __sexp__(self):
        pass


def _findvar(symbol, r_environment):
    rlib = openrlib.rlib
    return rlib.Rf_findVar(symbol,
                           r_environment)


def _findfun(symbol, r_environment):
    rlib = openrlib.rlib
    return rlib.Rf_findFun(symbol,
                           r_environment)


@ffi_proxy.callback(ffi_proxy._exec_findvar_in_frame_def,
                    openrlib._rinterface_cffi)
def _exec_findvar_in_frame(cdata):
    cdata_struct = openrlib.ffi.cast('struct RPY2_sym_env_data *', cdata)
    res = openrlib.rlib.Rf_findVarInFrame(
        cdata_struct.environment,
        cdata_struct.symbol
    )
    cdata_struct.data = res
    return


def findvar_in_frame(rho, symbol):
    """Safer wrapper around Rf_findVarInFrame()

    Run the function Rf_findVarInFrame() in R's C-API through
    R_ToplevelExec().

    Note: All arguments, and the object returned, are C-level
    R objects.

    Args:
    - rho: An R environment.
    - symbol: An R symbol (as returned by Rf_install())
    Returns:
    The object found.
    """
    # One would expect this to be like
    #   res = _rinterface._findfun(symbol, self.__sexp__._cdata)
    # but R's findfun will segfault if an error occurs while
    # accessing the matching object in the environment.
    exec_data = ffi.new(
        'struct RPY2_sym_env_data *',
        [symbol, rho, openrlib.rlib.R_NilValue]
    )
    _ = openrlib.rlib.R_ToplevelExec(
        openrlib.rlib._exec_findvar_in_frame,
        exec_data
    )
    if _ != openrlib.rlib.TRUE:
        raise embedded.RRuntimeError(
            'R C-API Rf_findVarInFrame()'
        )
    return exec_data.data


if FFI_MODE is ffi_proxy.InterfaceType.ABI:
    findvar_in_frame_wrap = openrlib.rlib.Rf_findVarInFrame
elif FFI_MODE is ffi_proxy.InterfaceType.API:
    findvar_in_frame_wrap = findvar_in_frame
else:
    raise ImportError('cffi mode unknown: %s' % FFI_MODE)


def _GET_DIM(robj):
    res = openrlib.rlib.Rf_getAttrib(robj,
                                     openrlib.rlib.R_DimSymbol)
    return res


def _GET_DIMNAMES(robj) -> FFI.CData:
    res = openrlib.rlib.Rf_getAttrib(robj,
                                     openrlib.rlib.R_DimNames)
    return res


def _GET_LEVELS(robj: FFI.CData) -> FFI.CData:
    res = openrlib.rlib.Rf_getAttrib(robj,
                                     openrlib.rlib.R_LevelsSymbol)
    return res


def _GET_NAMES(robj: FFI.CData) -> FFI.CData:
    res = openrlib.rlib.Rf_getAttrib(robj,
                                     openrlib.rlib.R_NamesSymbol)
    return res


def _TYPEOF(robj: FFI.CData) -> int:
    return robj.sxpinfo.type


def _SET_TYPEOF(robj: FFI.CData, v: int):
    robj.sxpinfo.type = v


def _NAMED(robj: FFI.CData) -> int:
    return robj.sxpinfo.named


def _string_getitem(cdata: FFI.CData, i: int) -> typing.Optional[str]:
    elt = openrlib.rlib.STRING_ELT(cdata, i)
    if elt == openrlib.rlib.R_NaString:
        res = None
    else:
        res = conversion._cchar_to_str(
            openrlib.rlib.R_CHAR(elt),
            conversion._R_ENC_PY[openrlib.rlib.Rf_getCharCE(elt)]
        )
    return res


# TODO: still used ?
def _string_setitem(cdata: FFI.CData, i: int, value_b) -> None:
    rlib = openrlib.rlib
    rlib.SET_STRING_ELT(
        cdata, i, rlib.Rf_mkCharCE(value_b, conversion._CE_DEFAULT_VALUE)
    )


def _has_slot(cdata: FFI.CData, name_b) -> bool:
    res = openrlib.rlib.R_has_slot(cdata, name_b)
    return bool(res)


def build_rcall(rfunction,
                args=[],
                kwargs=[]):
    rlib = openrlib.rlib
    with memorymanagement.rmemory() as rmemory:
        rcall = rmemory.protect(
            rlib.Rf_allocList(len(args)+len(kwargs)+1)
        )
        _SET_TYPEOF(rcall, rlib.LANGSXP)
        rlib.SETCAR(rcall, rfunction)
        item = rlib.CDR(rcall)
        for val in args:
            cdata = rmemory.protect(conversion._get_cdata(val))
            rlib.SETCAR(item, cdata)
            item = rlib.CDR(item)
        for key, val in kwargs:
            if key is not None:
                _assert_valid_slotname(key)
                rlib.SET_TAG(
                    item,
                    rlib.Rf_install(conversion._str_to_cchar(key)))
            cdata = rmemory.protect(conversion._get_cdata(val))
            rlib.SETCAR(item, cdata)
            item = rlib.CDR(item)
    return rcall


def _evaluated_promise(function):
    def _(*args, **kwargs):
        robj = function(*args, **kwargs)
        if _TYPEOF(robj) == openrlib.rlib.PROMSXP:
            robj = openrlib.rlib.Rf_eval(
                robj,
                openrlib.rlib.R_GlobalEnv)
        return robj
    return _


def _python_index_to_c(cdata: FFI.CData, i: int) -> int:
    """Compute the C value for a Python-style index.

    The function will translate a Python-style index that
    can be either positive or negative, if the later to
    indicate that indexing is relative to the end of the
    sequence, into a strictly positive or null index as
    use in C.

    Raises an exception IndexError if out of bounds."""

    size = openrlib.rlib.Rf_xlength(cdata)
    if i < 0:
        # x = [0,1,2,3]
        # x[-3] = x[size + (-3)] = x[4 - 3] = x[1] = 1
        # x[-2] = x[size + (-2)] = x[4 - 2] = x[2] = 2
        i = size + i
    if i >= size or i < 0:
        raise IndexError('index out of range')
    return i


# TODO: make it a general check for names or symbols ?
def _assert_valid_slotname(name: str) -> None:
    if not isinstance(name, str):
        raise ValueError('Invalid name %s' % repr(name))
    elif len(name) == 0:
        raise ValueError('The name cannot be an empty string')


def _list_attrs(cdata: FFI.CData) -> FFI.CData:
    rlib = openrlib.rlib
    attrs = rlib.ATTRIB(cdata)
    nvalues = rlib.Rf_length(attrs)
    if rlib.Rf_isList(cdata):
        namesattr = rlib.Rf_getAttrib(cdata, rlib.R_NamesSymbol)
        if namesattr != rlib.R_NilValue:
            nvalues += 1
    else:
        namesattr = rlib.R_NilValue

    with memorymanagement.rmemory() as rmemory:
        names = rmemory.protect(
            rlib.Rf_allocVector(rlib.STRSXP, nvalues))
        attr_i = 0
        if namesattr != rlib.R_NilValue:
            rlib.SET_STRING_ELT(names, attr_i,
                                rlib.PRINTNAME(rlib.R_NamesSymbol))
            attr_i += 1

        while attrs != rlib.R_NilValue:
            tag = rlib.TAG(attrs)
            if _TYPEOF(tag) == rlib.SYMSXP:
                rlib.SET_STRING_ELT(names, attr_i,
                                    rlib.PRINTNAME(tag))
            else:
                rlib.SET_STRING_ELT(
                    names,
                    attr_i,
                    rlib.R_BlankString
                )
            attrs = rlib.CDR(attrs)
            attr_i += 1
    return names


def _remove(name: FFI.CData, env: FFI.CData, inherits) -> FFI.CData:
    rlib = openrlib.rlib
    with memorymanagement.rmemory() as rmemory:
        internal = rmemory.protect(
            rlib.Rf_install(conversion._str_to_cchar('.Internal')))
        remove = rmemory.protect(
            rlib.Rf_install(conversion._str_to_cchar('remove')))
        args = rmemory.protect(rlib.Rf_lang4(remove, name,
                                             env, inherits))
        call = rmemory.protect(rlib.Rf_lang2(internal, args))
        # TODO: use tryEval instead and catch errors.
        res = rlib.Rf_eval(call, rlib.R_GlobalEnv)
    return res


def _geterrmessage() -> str:
    rlib = openrlib.rlib
    # TODO: use isString and installTrChar
    with memorymanagement.rmemory() as rmemory:
        symbol = rmemory.protect(
            rlib.Rf_install(
                conversion._str_to_cchar('geterrmessage'))
        )
        geterrmessage = _findvar(
            symbol,
            rlib.R_GlobalEnv)
        call_r = rlib.Rf_lang1(geterrmessage)
        res = rmemory.protect(
            rlib.Rf_eval(call_r, rlib.R_GlobalEnv)
        )
        res = _string_getitem(res, 0)
    return res


def serialize(cdata: FFI.CData, cdata_env: FFI.CData) -> FFI.CData:
    """Serialize an R object to an R string.

    Note that the R string returned is *not* protected from
    the R garbage collection."""

    rlib = openrlib.rlib

    with memorymanagement.rmemory() as rmemory:
        sym_serialize = rmemory.protect(
            rlib.Rf_install(conversion._str_to_cchar('serialize'))
        )
        func_serialize = rmemory.protect(
            _findfun(sym_serialize, rlib.R_BaseEnv))
        r_call = rmemory.protect(
            rlib.Rf_lang3(func_serialize, cdata, rlib.R_NilValue)
        )
        error_occured = ffi.new('int *', 0)
        res = rlib.R_tryEval(r_call,
                             cdata_env,
                             error_occured)
        if error_occured[0]:
            raise embedded.RRuntimeError(_geterrmessage())
        return res


def unserialize(cdata: FFI.CData, cdata_env: FFI.CData) -> FFI.CData:
    """Unserialize an R string to an R object.

    Note that the R object returned is *not* protected from
    the R garbage collection."""

    rlib = openrlib.rlib

    with memorymanagement.rmemory() as rmemory:
        sym_unserialize = rmemory.protect(
            rlib.Rf_install(
                conversion._str_to_cchar('unserialize'))
        )
        func_unserialize = rmemory.protect(_findfun(sym_unserialize,
                                                    rlib.R_BaseEnv))
        r_call = rmemory.protect(
            rlib.Rf_lang2(func_unserialize, cdata)
        )
        error_occured = ffi.new('int *', 0)
        res = rlib.R_tryEval(r_call,
                             cdata_env,
                             error_occured)
        if error_occured[0]:
            raise embedded.RRuntimeError(_geterrmessage())

        return res


@ffi_proxy.callback(ffi_proxy._evaluate_in_r_def,
                    openrlib._rinterface_cffi)
def _evaluate_in_r(rargs: FFI.CData) -> FFI.CData:
    # An uncaught exception in the boby of this function would
    # result in a segfault. we wrap it in a try-except an report
    # exceptions as logs.

    rlib = openrlib.rlib

    try:
        rargs = rlib.CDR(rargs)
        cdata = rlib.CAR(rargs)
        if (_TYPEOF(cdata) != rlib.EXTPTRSXP):
            # TODO: also check tag
            #    (rlib.R_ExternalPtrTag(sexp) == '.Python')
            logger.error('The fist item is not an R external pointer.')
            return rlib.R_NilValue
        handle = rlib.R_ExternalPtrAddr(cdata)
        func = ffi.from_handle(handle)

        pyargs = []
        pykwargs = {}
        rargs = rlib.CDR(rargs)
        while rargs != rlib.R_NilValue:
            cdata = rlib.CAR(rargs)
            if rlib.Rf_isNull(rlib.TAG(rargs)):
                # Unnamed argument
                pyargs.append(conversion._cdata_to_rinterface(cdata))
            else:
                # Named arguments
                rname = rlib.PRINTNAME(rlib.TAG(rargs))
                name = conversion._cchar_to_str(
                    rlib.R_CHAR(rname),
                    conversion._R_ENC_PY[openrlib.rlib.Rf_getCharCE(rname)]
                )
                pykwargs[name] = conversion._cdata_to_rinterface(cdata)
            rargs = rlib.CDR(rargs)

        res = func(*pyargs, **pykwargs)
        # The object is whatever the "rternalized" function `func`
        # is returning and we need to cast that result into a SEXP
        # that R's C API can handle. At the same time we need to ensure
        # that the R is:
        # - protected from garbage collection long enough to let the R
        #   code that called the rternalized function complete.
        # - eventually its memory is freed to prevent a leak.
        # To that end, we create a SEXP object to be returned that is
        # not managed by rpy2, leaving the object's lifespan under R's
        # sole control.
        if (
                hasattr(res, '_sexpobject') and
                isinstance(res._sexpobject, SexpCapsule)
        ):
            return res._sexpobject._cdata
        else:
            return conversion._python_to_cdata(res)
    except Exception as e:
        logger.error('%s: %s' % (type(e), e))
        return rlib.R_NilValue


def _register_external_symbols() -> None:
    python_cchar = ffi.new('char []', b'.Python')
    ffi_proxy = openrlib.ffi_proxy
    if (
            ffi_proxy.get_ffi_mode(openrlib._rinterface_cffi)
            ==
            ffi_proxy.InterfaceType.ABI
    ):
        python_callback = ffi.cast('DL_FUNC', _evaluate_in_r)
    else:
        python_callback = ffi.cast('DL_FUNC', openrlib.rlib._evaluate_in_r)
    externalmethods = ffi.new(
        'R_ExternalMethodDef[]',
        [[python_cchar,
          python_callback,
          -1],
         [ffi.NULL, ffi.NULL, 0]])
    openrlib.rlib.R_registerRoutines(
        openrlib.rlib.R_getEmbeddingDllInfo(),
        ffi.NULL,
        ffi.NULL,
        ffi.NULL,
        externalmethods
    )


class PARSING_STATUS(enum.Enum):
    PARSE_NULL = openrlib.rlib.PARSE_NULL
    PARSE_OK = openrlib.rlib.PARSE_OK
    PARSE_INCOMPLETE = openrlib.rlib.PARSE_INCOMPLETE
    PARSE_ERROR = openrlib.rlib.PARSE_ERROR
    PARSE_EOF = openrlib.rlib.PARSE_EOF


class RParsingError(Exception):

    def __init__(self, msg: str, status: PARSING_STATUS = None):
        full_msg = (
            '{msg} - {status}'
            .format(msg=msg, status=status)
        )
        super().__init__(full_msg)
        self.status = status


@ffi_proxy.callback(ffi_proxy._parsevector_wrap_def,
                    openrlib._rinterface_cffi)
def _parsevector_wrap(data: FFI.CData):
    try:
        cdata, num, status = ffi.from_handle(data)
        res = openrlib.rlib.R_ParseVector(
            cdata,  # text
            num,
            status,
            openrlib.rlib.R_NilValue)
    except Exception as e:
        res = openrlib.rlib.R_NilValue
        logger.error('_parsevector_wrap: %s', str(e))
    return res


# TODO: is this complete ?
@ffi_proxy.callback(ffi_proxy._handler_def,
                    openrlib._rinterface_cffi)
def _handler_wrap(cond, hdata):
    return openrlib.rlib.R_NilValue


if FFI_MODE is ffi_proxy.InterfaceType.ABI:
    _parsevector_wrap = _parsevector_wrap
    _handler_wrap = _handler_wrap
elif FFI_MODE is ffi_proxy.InterfaceType.API:
    _parsevector_wrap = openrlib.rlib._parsevector_wrap
    _handler_wrap = openrlib.rlib._handler_wrap
else:
    raise ImportError('cffi mode unknown: %s' % FFI_MODE)


def _parse(cdata: FFI.CData, num, rmemory) -> FFI.CData:
    status = ffi.new('ParseStatus[1]', None)
    data = ffi.new_handle((cdata, num, status))
    hdata = ffi.NULL
    res = rmemory.protect(
        openrlib.rlib.R_tryCatchError(
            _parsevector_wrap, data,
            _handler_wrap, hdata
        )
    )
    # TODO: design better handling of possible status:
    # PARSE_NULL,
    # PARSE_OK,
    # PARSE_INCOMPLETE,
    # PARSE_ERROR,
    # PARSE_EOF
    if status[0] != openrlib.rlib.PARSE_OK:
        raise RParsingError('Parsing status not OK',
                            status=PARSING_STATUS(status[0]))
    return res
