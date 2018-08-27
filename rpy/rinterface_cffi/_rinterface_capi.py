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
    # addr = int(ffi.cast('uintptr_t', cdata))
    count = _R_PRESERVED.get(cdata, 0)
    _R_PRESERVED[cdata] = count + 1


def _release(cdata):
    # addr = int(ffi.cast('uintptr_t', cdata))
    count = _R_PRESERVED[cdata] - 1
    if count == 0:
        del(_R_PRESERVED[cdata])


class SexpCapsule(object):

    __slots__ = ('_cdata', )
    
    def __init__(self, cdata):
        assert is_cdata_sexp(cdata)
        _preserve(cdata)
        self._cdata = cdata

    def __del__(self):
        _release(self._cdata)


class UnmanagedSexpCapsule(object):

    __slots__ = ('_cdata', )
    
    def __init__(self, cdata):
        assert is_cdata_sexp(cdata)
        self._cdata = cdata

        
def _findvar(name, r_environment):
    # TODO: use isStrinb and installTrChar
    name_b = name.encode('ASCII')
    res = rlib.Rf_findVar(rlib.Rf_install(ffi.new('char[]', name_b)),
                          r_environment)
    return res


def _findfun(name, r_environment):
    # TODO: use isStrinb and installTrChar
    name_b = name.encode('ASCII')
    res = rlib.Rf_findFun(rlib.Rf_install(ffi.new('char[]', name_b)),
                          r_environment)
    return res


def _findVarInFrame(name, r_environment):
    # TODO: use isStrinb and installTrChar
    name_b = name.encode('ASCII')
    res = rlib.Rf_findVarInFrame(r_environment,
                                 rlib.Rf_install(ffi.new('char[]', name_b)))
                                 
    return res


def _GET_CLASS(robj):
    res = rlib.Rf_getAttrib(robj,
                            rlib.R_ClassSymbol)
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


def _CHAR(x):
    return ffi.cast('const char *', rlib.STDVEC_DATAPTR(x))


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
    return ffi.string(_STRING_VALUE(rlib.STRING_ELT(cdata, i)))


def _string_setitem(cdata, i, value_b):
    rlib.SET_STRING_ELT(
        cdata, i, rlib.Rf_mkChar(value_b)
    )

def _has_slot(cdata, name_b):
    res = rlib.R_has_slot(cdata, name_b)
    return bool(res)


def _build_rcall(rfunction, *args, **kwargs):
    rcall = rlib.Rf_protect(
        rlib.Rf_allocList(len(args)+len(kwargs)+1)
    )
    _SET_TYPEOF(rcall, rlib.LANGSXP)
    try:
        rlib.SETCAR(rcall, rfunction)
        item = rlib.CDR(rcall)
        for val in args:
            rlib.SETCAR(item, val.__sexp__._cdata)
            item = rlib.CDR(item)
        for key, val in kwargs.items():
            rlib.SETTAG(item,
                        rlib.Rf_install(ffi.new('char[]', name_b)))
            rlib.SETCAR(item, val.__sexp__._cdata)
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
