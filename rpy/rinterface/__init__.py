import collections
import enum
import os
import sys
import warnings
from . import _rinterface_capi as _rinterface
from . import embedded


class RTYPES(enum.IntEnum):
    NILSXP     = _rinterface.rlib.NILSXP
    SYMSXP     = _rinterface.rlib.SYMSXP
    LISTSXP    = _rinterface.rlib.LISTSXP
    CLOSXP     = _rinterface.rlib.CLOSXP
    ENVSXP     = _rinterface.rlib.ENVSXP
    PROMSXP    = _rinterface.rlib.PROMSXP
    LANGSXP    = _rinterface.rlib.LANGSXP
    SPECIALSXP = _rinterface.rlib.SPECIALSXP
    BUILTINSXP = _rinterface.rlib.BUILTINSXP
    CHARSXP    = _rinterface.rlib.CHARSXP
    LGLSXP     = _rinterface.rlib.LGLSXP
    INTSXP     = _rinterface.rlib.INTSXP
    REALSXP    = _rinterface.rlib.REALSXP
    CPLXSXP    = _rinterface.rlib.CPLXSXP
    STRSXP     = _rinterface.rlib.STRSXP
    DOTSXP     = _rinterface.rlib.DOTSXP
    ANYSXP     = _rinterface.rlib.ANYSXP
    VECSXP     = _rinterface.rlib.VECSXP
    EXPRSXP    = _rinterface.rlib.EXPRSXP
    BCODESXP   = _rinterface.rlib.BCODESXP
    EXTPTRSXP  = _rinterface.rlib.EXTPTRSXP
    WEAKREFSXP = _rinterface.rlib.WEAKREFSXP
    RAWSXP     = _rinterface.rlib.RAWSXP
    S4SXP      = _rinterface.rlib.S4SXP
    
    NEWSXP     = _rinterface.rlib.NEWSXP
    FREESXP    = _rinterface.rlib.FREESXP
    
    FUNSXP     = _rinterface.rlib.FUNSXP


def _cdata_to_rinterface(function):
    def _(*args, **kwargs):
        cdata = function(*args, **kwargs)
        # TODO: test cdata is of of the expected type
        if _rinterface._TYPEOF(cdata) == RTYPES.NILSXP:
            res = NULL
        else:
            scaps = _rinterface.SexpCapsule(cdata)
            res = _R_RPY2_MAP.get(cdata.sxpinfo.type,
                                  Sexp)(scaps)
        return res
    return _


_evaluated_promise = _rinterface._evaluated_promise


@_cdata_to_rinterface
def parse(text, num=-1):
    if not isinstance(text, str):
        raise ValueError('text must be a string.')
    robj = StrSexpVector([text])
    return embedded._parse(robj.__sexp__._cdata, num)


class _NULL(object):

    __slots__ = ('_sexpobject', )

    def __init__(self):
        self._sexpobject = _rinterface.UnmanagedSexpCapsule(
            _rinterface.rlib.R_NilValue)

    def __repr__(self):
        return super().__repr__() + (' [%s]' % self.typeof)

    def __bool__(self):
        return False
    
    @property
    def __sexp__(self):
        return self._sexpobject

    @property
    def typeof(self):
        return RTYPES(_rinterface._TYPEOF(self.__sexp__._cdata))


class _MissingArg(object):

    __slots__ = ('_sexpobject', )

    def __init__(self):
        self._sexpobject = _rinterface.UnmanagedSexpCapsule(
            _rinterface.rlib.R_MissingArg)

    def __repr__(self):
        return super().__repr__() + (' [%s]' % self.typeof)

    def __bool__(self):
        return False
    
    @property
    def __sexp__(self):
        return self._sexpobject

    @property
    def typeof(self):
        return RTYPES(_rinterface._TYPEOF(self.__sexp__._cdata))


class Sexp(object):
    
    __slots__ = ('_sexpobject', )

    def __init__(self, sexp):
        if isinstance(sexp, Sexp):
            self._sexpobject = sexp.__sexp__
        elif isinstance(sexp, _rinterface.SexpCapsule):
            self._sexpobject = sexp
        else:
            raise ValueError('The constructor must be called '
                             'with that is an instance of rpy2.rinterface.Sexp '
                             'or an instance of rpy2.rinterface._rinterface.SexpCapsule')

    def __repr__(self):
        return super().__repr__() + (' [%s]' % self.typeof)

    @property
    def __sexp__(self):
        return self._sexpobject

    @__sexp__.setter
    def __sexp__(self, value):
        assert isinstance(value, _rinterface.SexpCapsule)
        if _rinterface._TYPEOF(value._cdata) != _rinterface._TYPEOF(self.__sexp__._cdata):
            raise ValueError('New capsule type mismatch: %s' %
                             RTYPES(value.typeof))
        self._sexpobject = value

    @property
    def __sexp_refcount__(self):
        return _rinterface._R_PRESERVED[
            _rinterface.get_rid(self.__sexp__._cdata)
        ]

    def __getstate__(self):
        ser = _rinterface.rlib.Rf_protect(
            _rinterface.serialize(self.__sexp__._cdata,
                                  globalenv.__sexp__._cdata)
        )
        n = _rinterface.rlib.Rf_xlength(ser)
        res = bytes(_rinterface.ffi.buffer(_rinterface.rlib.RAW(ser), n))
        _rinterface.rlib.Rf_unprotect(1)
        return res

    def __setstate__(self, state):
        self._sexpobject = unserialize(state)

    @property
    @_cdata_to_rinterface
    def rclass(self):
        return _rinterface._GET_CLASS(self.__sexp__._cdata)

    @rclass.setter
    def rclass(self, value):
        cdata = _rinterface._get_cdata(value)
        self.__sexp__ = _rinterface.SexpCapsule(
            _rinterface._SET_CLASS(self.__sexp__._cdata, cdata)
            )
        

    @property
    def rid(self):
        return _rinterface.get_rid(self.__sexp__._cdata)

    @property
    def typeof(self):
        return RTYPES(_rinterface._TYPEOF(self.__sexp__._cdata))
    
    @property
    def named(self):
        return _rinterface._NAMED(self.__sexp__._cdata)

    @_cdata_to_rinterface
    def list_attrs(self):
        return _rinterface._list_attrs(self.__sexp__._cdata)

    @_cdata_to_rinterface
    def do_slot(self, name):
        _rinterface._assert_valid_slotname(name)
        cchar = _rinterface._str_to_cchar(name)
        # TODO: protect ?
        name_r = _rinterface.rlib.Rf_install(cchar)
        if not _rinterface._has_slot(self.__sexp__._cdata, name_r):
            raise LookupError('%s (encoded to %s)' % (name, cchar))
        return _rinterface.rlib.R_do_slot(self.__sexp__._cdata, name_r)

    def do_slot_assign(self, name, value):
        _rinterface._assert_valid_slotname(name)
        cchar = _rinterface._str_to_cchar(name)
        name_r = _rinterface.rlib.Rf_install(cchar)
        _rinterface.rlib.R_do_slot_assign(self.__sexp__._cdata,
                                          name_r,
                                          value.__sexp__._cdata)

    # TODO: deprecate this ?
    def rsame(self, sexp):
        if not isinstance(sexp, Sexp):
            raise ValueError('Not an R object.')
        return self.__sexp__._cdata == sexp.__sexp__._cdata


class SexpSymbol(Sexp):
    
    def __init__(self, obj):
        if isinstance(obj, Sexp) or isinstance(obj, _rinterface.SexpCapsule):
            super().__init__(obj)
        elif isinstance(obj, str):
            name_cdata = _rinterface.ffi.new('char []', obj.encode('utf-8'))
            sexp = _rinterface.SexpCapsule(
                _rinterface.rlib.Rf_install(name_cdata))
            super().__init__(sexp)
        else:
            raise ValueError(
                'The constructor must be called '
                'with that is an instance of rpy2.rinterface.Sexp '
                'or an instance of rpy2.rinterface._rinterface.SexpCapsule')

    def __str__(self):
        return _rinterface._cchar_to_str(
            _rinterface._STRING_VALUE(
                self._sexpobject._cdata
            )
        )


class SexpEnvironment(Sexp):

    @_cdata_to_rinterface
    @_evaluated_promise
    def get(self, key, wantfun=False):
        # TODO: move check of R_UnboundValue to _rinterface ?
        if not (isinstance(key, str) and len(key)):
            raise ValueError('The key must be a non-empty string.')
        symbol = _rinterface.rlib.Rf_protect(
            _rinterface.rlib.Rf_install(_rinterface._str_to_cchar(key))
        )
        if wantfun:
            res = _rinterface._findfun(symbol, self.__sexp__._cdata)
        else:
            res = _rinterface._findvar(symbol, self.__sexp__._cdata)
        _rinterface.rlib.Rf_unprotect(1)
        if res == _rinterface.rlib.R_UnboundValue:
            raise KeyError("'%s' not found" % key)
        return res

    @_cdata_to_rinterface
    @_evaluated_promise
    def __getitem__(self, key):
        # TODO: move check of R_UnboundValue to _rinterface
        if not (isinstance(key, str) and len(key)):
            raise ValueError('The key must be a non-empty string.')
        symbol = _rinterface.rlib.Rf_protect(
            _rinterface.rlib.Rf_install(_rinterface._str_to_cchar(key))
        )
        res = _rinterface._findvar(symbol, self.__sexp__._cdata)
        _rinterface.rlib.Rf_unprotect(1)
        if res == _rinterface.rlib.R_UnboundValue:
            raise KeyError("'%s' not found" % key)
        return res

    def __setitem__(self, key, value):
        # TODO: move body to _rinterface-level function
        if not (isinstance(key, str) and len(key)):
            raise ValueError('The key must be a non-empty string.')
        if (self.__sexp__._cdata == _rinterface.rlib.R_BaseEnv) or \
           (self.__sexp__._cdata == _rinterface.rlib.R_EmptyEnv):
            raise ValueError('Cannot remove variables from the base or '
                             'empty environments.')
        # TODO: call to Rf_duplicate needed ?
        symbol = _rinterface.rlib.Rf_protect(
            _rinterface.rlib.Rf_install(_rinterface._str_to_cchar(key))
        )
        cdata_copy = _rinterface.rlib.Rf_protect(
            _rinterface.rlib.Rf_duplicate(value.__sexp__._cdata)
        )
        res = _rinterface.rlib.Rf_defineVar(symbol,
                                            cdata_copy,
                                            self.__sexp__._cdata)
        _rinterface.rlib.Rf_unprotect(2)

    def __len__(self):
        symbols = _rinterface.rlib.Rf_protect(
            _rinterface.rlib.R_lsInternal(self.__sexp__._cdata,
                                          _rinterface.rlib.TRUE)
            )
        n = _rinterface.rlib.Rf_xlength(symbols)
        _rinterface.rlib.Rf_unprotect(1)
        return n

    def __delitem__(self, key):
        # Testing that key is a non-empty string is implicitly
        # performed when checking that the key is in the environment. 
        if key not in self:
            raise KeyError("'%s' not found" % key)
        
        if self.__sexp__ == baseenv.__sexp__:
            raise ValueError('Values from the R base environment '
                             'cannot be removed.')
        # TODO: also check it is not R_EmpyEnv or R_BaseNamespace
        if self.is_locked():
            ValueError('Cannot remove an item from a locked '
                       'environment.')
        
        key_cdata = _rinterface.rlib.Rf_protect(
            _rinterface.rlib.Rf_mkString(_rinterface._str_to_cchar(key))
        )
        try:
            res_rm = _rinterface._remove(key_cdata, 
			                 self.__sexp__._cdata, 
			                 _rinterface.rlib.Rf_ScalarLogical(
                                             _rinterface.rlib.FALSE))
        finally:
            _rinterface.rlib.Rf_unprotect(1)

    @_cdata_to_rinterface
    def frame(self):
        # TODO: move body to _rinterface-level function
        return self.__sexp__._cdata.u.envsxp.frame

    @_cdata_to_rinterface
    def enclos(self):
        # TODO: move body to _rinterface-level function
        return self.__sexp__._cdata.u.envsxp.enclos
        
    def keys(self):
        symbols = _rinterface.rlib.Rf_protect(
            _rinterface.rlib.R_lsInternal(self.__sexp__._cdata,
                                          _rinterface.rlib.TRUE)
        )
        n = _rinterface.rlib.Rf_xlength(symbols)
        res = []
        for i in range(n):
            res.append(_rinterface._string_getitem(symbols, i))
        _rinterface.rlib.Rf_unprotect(1)
        for e in res:
            yield e

    def __iter__(self):
        return self.keys()

    def is_locked(self):
        return _rinterface.rlib.R_EnvironmentIsLocked(
            self.__sexp__._cdata)

    
class SexpPromise(Sexp):

    @_cdata_to_rinterface
    def eval(self, env=None):
        if not env:
            env = globalenv
        return _rinterface.rlib.Rf_eval(self.__sexp__._cdata, env)


# TODO: move to _rinterface-level function (as ABI / API compatibility
# will have API-defined code compile for efficiency).
def _populate_r_vector(iterable, r_vector, get_ptr, cast_value):
    c_array = get_ptr(r_vector)
    for i, v in enumerate(iterable):
        c_array[i] = cast_value(v)


class SexpVector(Sexp):

    def __init__(self, obj):
        if isinstance(obj, Sexp) or isinstance(obj, _rinterface.SexpCapsule):
            super().__init__(obj)
        elif isinstance(obj, collections.Sized):
            super().__init__(type(self).from_iterable(obj).__sexp__)
        else:
            raise ValueError('The constructor must be called '
                             'with that is an instance of rpy2.rinterface.Sexp '
                             'or an instance of rpy2.rinterface._rinterface.SexpCapsule')
        
    @classmethod
    @_cdata_to_rinterface
    def from_iterable(cls, iterable):
        n = len(iterable)
        r_vector = _rinterface.rlib.Rf_allocVector(
            cls._R_TYPE, n)
        _populate_r_vector(iterable,
                           r_vector,
                           cls._R_GET_PTR,
                           cls._CAST_IN)        
        return r_vector

    @_cdata_to_rinterface
    def __getitem__(self, i):
        i_c = _rinterface._python_index_to_c(self.__sexp__._cdata, i)
        return _rinterface.rlib.VECTOR_ELT(self.__sexp__._cdata, i_c)

    def __setitem__(self, i, value):
        i_c = _rinterface._python_index_to_c(self.__sexp__._cdata, i)
        _rinterface.rlib.SET_VECTOR_ELT(self.__sexp__._cdata, i_c,
                                        value)

    def __len__(self):
        return _rinterface.rlib.Rf_xlength(self.__sexp__._cdata)

    def index(self, item):
        for i, e in enumerate(self):
            if e == item:
                return i
        raise ValueError("'%s' is not in R vector" % item)


class BoolSexpVector(SexpVector):
    
    _R_TYPE = _rinterface.rlib.LGLSXP
    _R_GET_PTR = _rinterface._LOGICAL
    _CAST_IN = bool

    def __getitem__(self, i):
        i_c = _rinterface._python_index_to_c(self.__sexp__._cdata, i)
        return bool(_rinterface.rlib.LOGICAL_ELT(self.__sexp__._cdata, i_c))

    def __setitem__(self, i, value):
        i_c = _rinterface._python_index_to_c(self.__sexp__._cdata ,i)
        _rinterface.rlib.SET_LOGICAL_ELT(self.__sexp__._cdata, i_c,
                                         bool)


class IntSexpVector(SexpVector):

    _R_TYPE = _rinterface.rlib.INTSXP
    _R_GET_PTR = _rinterface._INTEGER
    _CAST_IN = int
    
    def __getitem__(self, i):
        i_c = _rinterface._python_index_to_c(self.__sexp__._cdata, i)
        return _rinterface.rlib.INTEGER_ELT(self.__sexp__._cdata, i_c)

    def __setitem__(self, i, value):
        i_c = _rinterface._python_index_to_c(self.__sexp__._cdata, i)
        _rinterface.rlib.SET_INTEGER_ELT(self.__sexp__._cdata, i_c,
                                         int(value))
        

class FloatSexpVector(SexpVector):

    _R_TYPE = _rinterface.rlib.REALSXP
    _R_GET_PTR = _rinterface._REAL
    _CAST_IN = float

    def __getitem__(self, i):
        i_c = _rinterface._python_index_to_c(self.__sexp__._cdata, i)
        return _rinterface.rlib.REAL_ELT(self.__sexp__._cdata, i_c)

    def __setitem__(self, i, value):
        i_c = _rinterface._python_index_to_c(self.__sexp__._cdata, i)
        _rinterface.rlib.SET_REAL_ELT(self.__sexp__._cdata, i_c,
                                      float(value))


class CETYPE(enum.Enum):
    CE_NATIVE = 0
    CE_UTF8   = 1
    CE_LATIN1 = 2
    CE_BYTES  = 3
    CE_SYMBOL = 5
    CE_ANY    = 99


class CharSexp(Sexp):

    _R_TYPE = _rinterface.rlib.CHARSXP

    @property
    def encoding(self):
        return CETYPE(
            _rinterface.rlib.Rf_getCharCE(self.__sexp__._cdata)
        )

    def nchar(self):
        # nchar_type is not parse properly by cffi ?
        raise NotImplementedError()


class StrSexpVector(SexpVector):

    _R_TYPE = _rinterface.rlib.STRSXP
    _R_GET_PTR = _rinterface._STRING_PTR
    _CAST_IN = _rinterface._str_to_charsxp

    def __getitem__(self, i):
        i_c = _rinterface._python_index_to_c(self.__sexp__._cdata, i)
        res = _rinterface._string_getitem(self.__sexp__._cdata, i_c)
        return res

    def __setitem__(self, i, value):
        i_c = _rinterface._python_index_to_c(self.__sexp__._cdata, i)
        _rinterface._string_setitem(
            self.__sexp__._cdata, i_c,
            _rinterface._str_to_charsxp(value)
        )

    def get_charsxp(self, i):
        i_c = _rinterface._python_index_to_c(self.__sexp__._cdata, i)
        return CharSexp(
            _rinterface.SexpCapsule(
                _rinterface.rlib.STRING_ELT(self.__sexp__._cdata, i_c)
            )
        )


class ExprSexpVector(SexpVector):
    _R_TYPE = _rinterface.rlib.LANGSXP
    _R_GET_PTR = None
    _CAST_IN = None


class LangSexpVector(SexpVector):
    _R_TYPE = _rinterface.rlib.LANGSXP
    _R_GET_PTR = None
    _CAST_IN = None

    @_cdata_to_rinterface
    def __getitem__(self, i):
        i_c = _rinterface._python_index_to_c(self.__sexp__._cdata, i)
        return _rinterface.rlib.CAR(
            _rinterface.rlib.Rf_nthcdr(self.__sexp__._cdata, i_c)
        )

    def __setitem__(self, i, value):
        i_c = _rinterface._python_index_to_c(self.__sexp__._cdata, i)
        _rinterface.rlib.SETCAR(
            _rinterface.rlib.Rf_nthcdr(self.__sexp__._cdata, i_c),
            value.__sexp__._cdata
        )

            
def _geterrmessage():
    # TODO: use isStrinb and installTrChar
    symbol = _rinterface.rlib.Rf_protect(
        _rinterface.rlib.Rf_install(
            _rinterface._str_to_cchar('geterrmessage')))
    geterrmessage = _rinterface._findvar(
        symbol,
        globalenv.__sexp__._cdata)
    _rinterface.rlib.Rf_unprotect(1)
    call_r = _rinterface.rlib.Rf_lang1(geterrmessage)
    res = _rinterface.rlib.Rf_protect(
        _rinterface.rlib.Rf_eval(call_r, globalenv.__sexp__._cdata)
    )
    res = _rinterface._string_getitem(res, 0)
    _rinterface.rlib.Rf_unprotect(1)
    return res
    

class SexpClosure(Sexp):
    
    @_cdata_to_rinterface
    def __call__(self, *args, **kwargs):
        error_occured = _rinterface.ffi.new('int *', 0)
        call_r = _rinterface.build_rcall(self.__sexp__._cdata, args, kwargs)
        res = _rinterface.rlib.Rf_protect(
            _rinterface.rlib.R_tryEval(call_r,
                                       globalenv.__sexp__._cdata,
                                       error_occured))
        try:
            if error_occured[0]:
                raise _rinterface.RRuntimeError(_geterrmessage())
        finally:
            _rinterface.rlib.Rf_unprotect(1)
        return res

    @_cdata_to_rinterface
    def rcall(self, mapping, environment):
        # TODO: check mapping has a method "items"
        assert isinstance(environment, SexpEnvironment)
        error_occured = _rinterface.ffi.new('int *', 0)
        call_r = _rinterface.build_rcall(self.__sexp__._cdata, [], mapping)
        res = _rinterface.rlib.R_tryEval(call_r,
                                         environment.__sexp__._cdata,
                                         error_occured)
        if error_occured[0]:
            raise _rinterface.RRuntimeError(_geterrmessage())
        return res

    @property
    @_cdata_to_rinterface
    def closureenv(self):
        return _rinterface.rlib.CLOENV(self.__sexp__._cdata)


def make_extptr(obj, tag, protected):
    ptr = _rinterface.ffi.new_handle(obj)
    cdata = _rinterface.rlib.Rf_protect(
        _rinterface.rlib.R_MakeExternalPtr(
            ptr,
            tag,
            protected))
    _rinterface.rlib.R_RegisterCFinalizer(
        cdata,
        _rinterface._capsule_finalizer)
    res = _rinterface.SexpCapsuleWithPassenger(cdata, (obj, ptr))
    _rinterface.rlib.Rf_unprotect(1)
    return res


class SexpExtPtr(Sexp):

    TYPE_TAG = 'Python'

    def __init__(self, callable, tag=TYPE_TAG,
                 protected=_rinterface.rlib.R_NilValue):
        scaps = make_extptr(callable,
                            _rinterface._str_to_cchar(self.TYPE_TAG),
                            protected)
        super().__init__(scaps)


# TODO: Only use rinterface-level ?
_R_RPY2_MAP = {
    _rinterface.rlib.EXPRSXP: ExprSexpVector,
    _rinterface.rlib.LANGSXP: LangSexpVector,
    _rinterface.rlib.ENVSXP: SexpEnvironment,
    _rinterface.rlib.LGLSXP: BoolSexpVector,
    _rinterface.rlib.INTSXP: IntSexpVector,
    _rinterface.rlib.REALSXP: FloatSexpVector,
    _rinterface.rlib.STRSXP: StrSexpVector,
    _rinterface.rlib.CLOSXP: SexpClosure,
    _rinterface.rlib.BUILTINSXP: SexpClosure
    }


class RRuntimeWarning(RuntimeWarning):
    pass


baseenv = None
globalenv = None
NULL = None
MISSING_ARG = None


def initr():
    status = embedded._initr()
    _rinterface._register_external_symbols()
    _post_initr_setup()
    return status


def _post_initr_setup():
    
    global baseenv
    baseenv = SexpEnvironment(
        _rinterface.SexpCapsule(_rinterface.rlib.R_BaseEnv)
    )

    global globalenv
    globalenv = SexpEnvironment(
        _rinterface.SexpCapsule(_rinterface.rlib.R_GlobalEnv)
    )

    global NULL    
    NULL = _NULL()

    global MISSING_ARG
    MISSING_ARG = _MissingArg()


def unserialize(state):
    n = len(state)
    cdata = _rinterface.rlib.Rf_protect(
        _rinterface.rlib.Rf_allocVector(_rinterface.rlib.RAWSXP, n))
    _rinterface.ffi.memmove(
        _rinterface.rlib.RAW(cdata), state, n)
    ser = _rinterface.rlib.Rf_protect(
        _rinterface.unserialize(cdata, globalenv.__sexp__._cdata)
    )
    res = _rinterface.SexpCapsule(ser)
    _rinterface.rlib.Rf_unprotect(2)
    return res


def rternalize(function):
    """ Takes an arbitrary Python function and wrap it
    in such a way that it can be called from the R side. """
    assert callable(function) 
    rpy_fun = SexpExtPtr(function)
    #FIXME: this is a hack. Find a better way.
    template = parse('function(...) { .External(".Python", foo, ...) }')
    template[0][2][1][2] = rpy_fun
    return baseenv['eval'](template)

    
