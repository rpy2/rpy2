# TODO: make it cffi-buildable with conditional function definition
# (Python if ABI, C if API)
import os
from _rinterface_cffi import ffi
import _cffi_backend
import rpy2.situation

R_HOME = rpy2.situation.get_r_home()
lib_path = os.path.join(R_HOME, "lib", "libR.so")
rlib = ffi.dlopen(lib_path)

_R_PRESERVED = dict()


def get_rid(cdata):
    return int(ffi.cast('uintptr_t', cdata))


def protected_rids():
    return tuple(
        (get_rid(k), v) for k, v in _R_PRESERVED.items()
        )


def is_cdata_sexp(obj):
    if (isinstance(obj, ffi.CData) and
        ffi.typeof(obj).cname == 'struct SEXPREC *'):
        return True
    else:
        return False


def _preserve(cdata):
    addr = int(ffi.cast('uintptr_t', cdata))
    count = _R_PRESERVED.get(addr, 0)
    if count == 0:
        rlib.R_PreserveObject(cdata)
    _R_PRESERVED[addr] = count + 1


def _release(cdata):
    addr = int(ffi.cast('uintptr_t', cdata))
    count = _R_PRESERVED[addr] - 1
    if count == 0:
        del(_R_PRESERVED[addr])
        rlib.R_ReleaseObject(cdata)
    else:
        _R_PRESERVED[addr] = count


class SexpCapsule(object):

    __slots__ = ('_cdata', )
    
    def __init__(self, cdata):
        assert is_cdata_sexp(cdata)
        _preserve(cdata)
        self._cdata = cdata

    def __del__(self):
        _release(self._cdata)

    @property
    def typeof(self):
        return _TYPEOF(self._cdata)

    @property
    def rid(self):
        return get_rid(self._cdata)


class UnmanagedSexpCapsule(object):

    __slots__ = ('_cdata', )
    
    def __init__(self, cdata):
        assert is_cdata_sexp(cdata)
        self._cdata = cdata


def _str_to_cchar(s, encoding='ASCII'):
    # TODO: use isStrinb and installTrChar
    b = s.encode(encoding)
    return ffi.new('char[]', b)


def _cchar_to_str(c, encoding='ASCII'):
    # TODO: use isStrinb and installTrChar
    s = ffi.string(c).decode(encoding)
    return s


def _cchar_to_str_with_maxlen(c, maxlen):
    # TODO: use isStrinb and installTrChar
    s = ffi.string(c, maxlen).decode('ASCII')
    return s


def _findvar(symbol, r_environment):
    res = rlib.Rf_protect(rlib.Rf_findVar(symbol,
                                          r_environment))
    rlib.Rf_unprotect(1)
    return res


def _findfun(symbol, r_environment):
    res = rlib.Rf_protect(rlib.Rf_findFun(symbol,
                                          r_environment))
    rlib.Rf_unprotect(1)
    return res


def _findVarInFrame(symbol, r_environment):
    res = rlib.Rf_protect(rlib.Rf_findVarInFrame(r_environment, symbol))
    rlib.Rf_unprotect(1)
    return res


def _GET_CLASS(robj):
    res = rlib.Rf_getAttrib(robj,
                            rlib.R_ClassSymbol)
    return res


def _SET_CLASS(robj, value):
    res = rlib.Rf_setAttrib(robj,
                            rlib.R_ClassSymbol,
                            value)
    return res


def _GET_DIM(robj):
    res = rlib.Rf_getAttrib(robj,
                            rlib.R_DimSymbol)
    return res


def _GET_DIMNAMES(robj):
    res = rlib.Rf_getAttrib(robj,
                            rlib.R_DimNames)
    return res


def _GET_LEVELS(robj):
    res = rlib.Rf_getAttrib(robj,
                            rlib.R_LevelsSymbol)
    return res


def _GET_NAMES(robj):
    res = rlib.Rf_getAttrib(robj,
                            rlib.R_NamesSymbol)
    return res


def _TYPEOF(robj):
    return robj.sxpinfo.type


def _SET_TYPEOF(robj, v):
    robj.sxpinfo.type = v


def _NAMED(robj):
    return robj.sxpinfo.named


def _LOGICAL(x):
    return ffi.cast('int *', rlib.DATAPTR(x))


def _INTEGER(x):
    return ffi.cast('int *', rlib.DATAPTR(x))


def _RAW(x):
    return ffi.cast('Rbyte *', rlib.DATAPTR(x))


def _REAL(robj):
    return ffi.cast('double *', rlib.DATAPTR(robj))


def _VECTOR_ELT(robj, i):
    return ffi.cast('SEXP *', rlib.DATAPTR(robj))[i]


def _STRING_PTR(robj):
    return ffi.cast('SEXP *', rlib.DATAPTR(robj))


def _VECTOR_PTR(robj):
    return ffi.cast('SEXP *', rlib.DATAPTR(robj))


def _STRING_VALUE(robj):
    return rlib.R_CHAR(rlib.Rf_asChar(robj))


def _string_getitem(cdata, i):
    return _cchar_to_str(
        rlib.R_CHAR(rlib.STRING_ELT(cdata, i))
    )


def _string_setitem(cdata, i, value_b):
    rlib.SET_STRING_ELT(
        cdata, i, rlib.Rf_mkChar(value_b)
    )


def _has_slot(cdata, name_b):
    res = rlib.R_has_slot(cdata, name_b)
    return bool(res)


# TODO: can scalars in R's C API be used ? 
def _int_to_sexp(val):
    # TODO: test value is not too large for R's ints
    s = rlib.Rf_protect(rlib.Rf_allocVector(rlib.INTSXP, 1))
    rlib.SET_INTEGER_ELT(s, 1, val)
    rlib.Rf_unprotect(1)
    return s


def _bool_to_sexp(val):
    # TODO: test value is not too large for R's ints
    s = rlib.Rf_protect(rlib.Rf_allocVector(rlib.LGLSXP, 1))
    rlib.SET_LOGICAL_ELT(s, 1, int(val))
    rlib.Rf_unprotect(1)
    return s


def _float_to_sexp(val):
    s = rlib.Rf_protect(rlib.Rf_allocVector(rlib.REALSXP, 1))
    rlib.SET_REAL_ELT(s, 1, val)
    rlib.Rf_unprotect(1)
    return s

# {
#     'ASCII'
#     'latin-1': rlib.cetype_t.CE_LATIN1,
#     'utf-8': rlib.cetype_t.CE_UTF8,
# }

def _str_to_charsxp(val):
    if val is None:
        s = rlib.R_NaString
    else:
        cchar = _str_to_cchar(val)
        s = rlib.Rf_mkCharLenCE(cchar, len(cchar))
    return s


def _str_to_sexp(val):
    cchar = _str_to_cchar(val)
    s = rlib.Rf_install(cchar)
    return s


PY_R_MAP = {
    int: _int_to_sexp,
    float: _float_to_sexp,
    bool: _bool_to_sexp,
    str: _str_to_sexp,
    complex: None
    }


def _get_cdata(obj):
    cast = PY_R_MAP.get(type(obj))
    if cast is None:
        try:
            cdata = obj.__sexp__._cdata
        except AttributeError as ae:
            raise ValueError('Not an rpy2 R object and unable '
                             'to cast it into one: %s' % repr(obj))
    else:
        cdata = cast(obj)
    return cdata


def build_rcall(rfunction, args=[], kwargs={}):
    rcall = rlib.Rf_protect(
        rlib.Rf_allocList(len(args)+len(kwargs)+1)
    )
    _SET_TYPEOF(rcall, rlib.LANGSXP)
    try:
        rlib.SETCAR(rcall, rfunction)
        item = rlib.CDR(rcall)
        for val in args:
            cast = PY_R_MAP.get(type(val))
            if cast is None:
                try:
                    cdata = val.__sexp__._cdata
                except AttributeError as ae:
                    raise ValueError('Not an rpy2 R object and unable '
                                     'to cast it into one: %s' % repr(val))
                rlib.SETCAR(item, cdata)
            else:
                cdata = rlib.Rf_protect(cast(val))
                rlib.SETCAR(item, cdata)
                rlib.Rf_unprotect(1)
            item = rlib.CDR(item)
        for key, val in kwargs.items():
            if key is not None:
                _assert_valid_slotname(key)
                rlib.SET_TAG(item,
                             rlib.Rf_install(_str_to_cchar(key)))
            cast = PY_R_MAP.get(type(val))
            if cast is None:
                try:
                    cdata = val.__sexp__._cdata
                except AttributeError as ae:
                    raise ValueError('Not an rpy2 R object and unable '
                                     'to cast it into one: %s' % repr(val))
                rlib.SETCAR(item, cdata)
            else:
                cdata = rlib.Rf_protect(cast(val))
                rlib.SETCAR(item, cdata)
                rlib.Rf_unprotect(1)
            item = rlib.CDR(item)        
    finally:
        rlib.Rf_unprotect(1)
    return rcall


def _evaluated_promise(function):
    def _(*args, **kwargs):
        robj = function(*args, **kwargs)
        if _TYPEOF(robj) == rlib.PROMSXP:
            robj = rlib.Rf_eval(robj, rlib.R_GlobalEnv)
        return robj
    return _


def _python_index_to_c(cdata, i):
    """Compulte the C value for a Python-style index.
    Raises an IndexError exception if out of bounds."""
    size = rlib.Rf_xlength(cdata)
    if i < 0:
        i = size - i
    if i >= size or i < 0:
        raise IndexError('index out of range')
    return i


# TODO: make it a general check for names or symbols ?
def _assert_valid_slotname(name):
    if not isinstance(name, str):
        raise ValueError('Invalid name %s' % repr(name))
    elif len(name) == 0:
        raise ValueError('The name cannot be an empty string')

def _list_attrs(cdata):
    attrs = rlib.ATTRIB(cdata);
    nvalues = rlib.Rf_length(attrs)
    res = rlib.Rf_allocVector(rlib.STRSXP, nvalues)
    rlib.Rf_protect(res)

    attr_i = 0
    while attrs != rlib.R_NilValue:
        if rlib.TAG(attrs) == rlib.R_NilValue:
            rlib.SET_STRING_ELT(res, attr_i, rlib.R_BlankString)
        else:
            rlib.SET_STRING_ELT(res, attr_i, rlib.PRINTNAME(rlib.TAG(attrs)))
        attrs = rlib.CDR(attrs);
        attr_i += 1  
    rlib.Rf_unprotect(1)
    return res


def _remove(name, env, inherits):
    internal = rlib.Rf_protect(rlib.Rf_install(_str_to_cchar('.Internal')))
    remove = rlib.Rf_protect(rlib.Rf_install(_str_to_cchar('remove')))
    args = rlib.Rf_protect(rlib.Rf_lang4(remove, name,
                                         env, inherits))
    call = rlib.Rf_protect(rlib.Rf_lang2(internal, args))
    # TODO: use tryEval instead and catch errors.
    res = rlib.Rf_eval(call, rlib.R_GlobalEnv)
    rlib.Rf_unprotect(4)
    return res


class RRuntimeError(Exception):
    pass


def serialize(cdata, cdata_env):
    sym_serialize = rlib.Rf_protect(
        rlib.Rf_install(_str_to_cchar('serialize'))
    )
    func_serialize = rlib.Rf_protect(_findfun(sym_serialize, rlib.R_BaseEnv))
    rlib.Rf_unprotect(1)
    r_call = rlib.Rf_protect(
        rlib.Rf_lang3(func_serialize, cdata, rlib.R_NilValue)
    )
    error_occured = ffi.new('int *', 0)
    res = rlib.R_tryEval(r_call,
                         cdata_env,
                         error_occured)
    if error_occured[0]:
        rlib.Rf_unprotect(2)
        raise RRuntimeError(_geterrmessage())

    rlib.Rf_unprotect(2)
    return res


def unserialize(cdata, cdata_env):
    sym_unserialize = rlib.Rf_protect(
        rlib.Rf_install(_str_to_cchar('unserialize'))
    )
    func_unserialize = rlib.Rf_protect(_findfun(sym_unserialize,
                                                rlib.R_BaseEnv))
    rlib.Rf_unprotect(1)
    r_call = rlib.Rf_protect(
        rlib.Rf_lang2(func_unserialize, cdata)
    )
    error_occured = ffi.new('int *', 0)
    res = rlib.R_tryEval(r_call,
                         cdata_env,
                         error_occured)
    if error_occured[0]:
        rlib.Rf_unprotect(2)
        raise RRuntimeError(_geterrmessage())

    rlib.Rf_unprotect(2)
    return res
    
