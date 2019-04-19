# TODO: make it cffi-buildable with conditional function definition
# (Python if ABI, C if API)
import enum
import logging
import warnings
from . import openrlib
from _rinterface_cffi import ffi
from . import conversion
from . import embedded
from . import memorymanagement

logger = logging.getLogger(__name__)

# TODO: How can I reliably get MAX_INT from limits.h ?
_MAX_INT = 2**32-1

_R_PRESERVED = dict()
_PY_PASSENGER = dict()


def get_rid(cdata) -> int:
    """Get the identifier for the R object.

    This is intended to be like Python's `id()`, but
    for R objects mapped by rpy2."""
    return int(ffi.cast('uintptr_t', cdata))


def protected_rids():
    """Sequence of R IDs protected from collection by rpy2."""
    keys = tuple(_R_PRESERVED.keys())
    res = []
    for k in keys:
        v = _R_PRESERVED.get(k)
        if v:
            res.append((get_rid(k), v))
    return tuple(res)


def is_cdata_sexp(obj) -> bool:
    """Is the object a cffi `CData` object pointing to an R object ?"""
    if (isinstance(obj, ffi.CData) and
            ffi.typeof(obj).cname == 'struct SEXPREC *'):
        return True
    else:
        return False


def _preserve(cdata):
    addr = int(ffi.cast('uintptr_t', cdata))
    count = _R_PRESERVED.get(addr, 0)
    if count == 0:
        openrlib.rlib.R_PreserveObject(cdata)
    _R_PRESERVED[addr] = count + 1
    return addr


def _release(cdata):
    addr = int(ffi.cast('uintptr_t', cdata))
    count = _R_PRESERVED[addr] - 1
    if count == 0:
        del(_R_PRESERVED[addr])
        openrlib.rlib.R_ReleaseObject(cdata)
    else:
        _R_PRESERVED[addr] = count


@ffi.callback('void (SEXP)')
def _capsule_finalizer(cdata):
    try:
        openrlib.rlib.R_ClearExternalPtr(cdata)
    except Exception as e:
        warnings.warn('Exception downgraded to warning: %s' % str(e))


class UnmanagedSexpCapsule(object):

    def __init__(self, cdata):
        assert is_cdata_sexp(cdata)
        self._cdata = cdata

    @property
    def typeof(self):
        return _TYPEOF(self._cdata)

    @property
    def rid(self) -> int:
        return get_rid(self._cdata)


class SexpCapsule(UnmanagedSexpCapsule):

    __slots__ = ('_cdata', )

    def __init__(self, cdata):
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

    def __init__(self, cdata, passenger, ptr):
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


def _findvar(symbol, r_environment):
    rlib = openrlib.rlib
    return rlib.Rf_findVar(symbol,
                           r_environment)


def _findfun(symbol, r_environment):
    rlib = openrlib.rlib
    return rlib.Rf_findFun(symbol,
                           r_environment)


def _findVarInFrame(symbol, r_environment):
    return openrlib.rlib.Rf_findVarInFrame(r_environment, symbol)


def _GET_DIM(robj):
    res = openrlib.rlib.Rf_getAttrib(robj,
                                     openrlib.rlib.R_DimSymbol)
    return res


def _GET_DIMNAMES(robj):
    res = openrlib.rlib.Rf_getAttrib(robj,
                                     openrlib.rlib.R_DimNames)
    return res


def _GET_LEVELS(robj):
    res = openrlib.rlib.Rf_getAttrib(robj,
                                     openrlib.rlib.R_LevelsSymbol)
    return res


def _GET_NAMES(robj):
    res = openrlib.rlib.Rf_getAttrib(robj,
                                     openrlib.rlib.R_NamesSymbol)
    return res


def _TYPEOF(robj):
    return robj.sxpinfo.type


def _SET_TYPEOF(robj, v):
    robj.sxpinfo.type = v


def _NAMED(robj):
    return robj.sxpinfo.named


def _string_getitem(cdata, i):
    rlib = openrlib.rlib
    return conversion._cchar_to_str(
        rlib.R_CHAR(rlib.STRING_ELT(cdata, i))
    )


# TODO: still used ?
def _string_setitem(cdata, i, value_b):
    rlib = openrlib.rlib
    rlib.SET_STRING_ELT(
        cdata, i, rlib.Rf_mkCharCE(value_b, conversion._CE_UTF8)
    )


def _has_slot(cdata, name_b):
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


def _python_index_to_c(cdata, i: int) -> int:
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
def _assert_valid_slotname(name: str):
    if not isinstance(name, str):
        raise ValueError('Invalid name %s' % repr(name))
    elif len(name) == 0:
        raise ValueError('The name cannot be an empty string')


def _list_attrs(cdata):
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


def _remove(name, env, inherits):
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


def _geterrmessage():
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


def serialize(cdata, cdata_env):
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


def unserialize(cdata, cdata_env):
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


@ffi.callback('SEXP (SEXP args)')
def _evaluate_in_r(rargs):
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
                name = conversion._cchar_to_str(
                    rlib.R_CHAR(rlib.PRINTNAME(rlib.TAG(rargs)))
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
    externalmethods = ffi.new(
        'R_ExternalMethodDef[]',
        [[python_cchar,
          ffi.cast('DL_FUNC', _evaluate_in_r),
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

    def __init__(self, msg: str, status: int):
        super().__init__(msg)
        self.status = status


def _parse(cdata, num):
    rlib = openrlib.rlib
    status = ffi.new('ParseStatus[1]', None)
    res = rlib.Rf_protect(
        rlib.R_ParseVector(
            cdata,  # text
            num,
            status,
            rlib.R_NilValue)
    )
    # TODO: design better handling of possible status:
    # PARSE_NULL,
    # PARSE_OK,
    # PARSE_INCOMPLETE,
    # PARSE_ERROR,
    # PARSE_EOF
    if status[0] != rlib.PARSE_OK:
        rlib.Rf_unprotect(1)
        raise RParsingError('R parsing', PARSING_STATUS(status[0]))
    rlib.Rf_unprotect(1)
    return res
