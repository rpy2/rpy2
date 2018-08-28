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
    return embedded._parse(text.__sexp__._cdata, num)

class _NULL(object):

    __slots__ = ('_sexpobject', )

    def __init__(self):
        self._sexpobject = _rinterface.UnmanagedSexpCapsule(_rinterface.rlib.R_NilValue)

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
                             RTYPES(_rinterface._TYPEOF(value._cdata)))
        self._sexpobject = value

    @property
    def __sexp_refcount__(self):
        return _rinterface._R_PRESERVED[self.__sexp__._cdata]
    
    @property
    @_cdata_to_rinterface
    def rclass(self):
        return _rinterface._GET_CLASS(self.__sexp__._cdata)

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
        # TODO: use isString and installTrChar
        name_b = name.encode('ASCII')
        name_r = _rinterface.rlib.Rf_install(_rinterface.ffi.new('char[]', name_b))
        if not _rinterface._has_slot(self.__sexp__._cdata, name_r):
            raise LookupError('%s (encoded to %s)' % (name, name_b))
        return _rinterface.rlib.R_do_slot(self.__sexp__._cdata, name_r)

    def do_slot_assign(self, name, value):
        _rinterface._assert_valid_slotname(name)
        # TODO: use isStrinb and installTrChar
        name_b = name.encode('ASCII')
        name_r = _rinterface.rlib.Rf_install(_rinterface.ffi.new('char[]', name_b))
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
            name_cdata = _rinterface.ffi.new('char []', obj.encode('ASCII'))
            sexp = _rinterface.SexpCapsule(_rinterface.rlib.Rf_install(name_cdata))
            super().__init__(sexp)
        else:
            raise ValueError('The constructor must be called '
                             'with that is an instance of rpy2.rinterface.Sexp '
                             'or an instance of rpy2.rinterface._rinterface.SexpCapsule')

    def __str__(self):
        return _rinterface.ffi.string(
            _rinterface._STRING_VALUE(
                self._sexpobject._cdata
            )
        ).decode('ASCII')


class SexpEnvironment(Sexp):

    @_cdata_to_rinterface
    @_evaluated_promise
    def get(self, key, wantfun=False):
        # TODO: move check of R_UnboundValue to _rinterface ?
        if not (isinstance(key, str) and len(key)):
            raise ValueError('The key must be a non-empty string.')
        if wantfun:
            res = _rinterface._findfun(key, self.__sexp__._cdata)
        else:
            res = _rinterface._findvar(key, self.__sexp__._cdata)
        if res == _rinterface.rlib.R_UnboundValue:
            raise KeyError("'%s' not found" % key)
        return res

    @_cdata_to_rinterface
    @_evaluated_promise
    def __getitem__(self, key):
        # TODO: move check of R_UnboundValue to _rinterface
        if not (isinstance(key, str) and len(key)):
            raise ValueError('The key must be a non-empty string.')
        res = _rinterface._findvar(key, self.__sexp__._cdata)
        if res == _rinterface.rlib.R_UnboundValue:
            raise KeyError("'%s' not found" % key)
        return res

    def __setitem__(self, key, value):
        # TODO: move body to _rinterface-level function
        if not (isinstance(key, str) and len(key)):
            raise ValueError('The key must be a non-empty string.')
        if (self.__sexp__._cdata == _rinterface.rlib.R_BaseEnv) or \
           (self.__sexp__._cdata == _rinterface.rlib.R_EmptyEnv):
            raise ValueError('Cannot remove variables from the base or empty environments.')
        # TODO: call to Rf_duplicate needed ?
        sym = _rinterface.rlib.Rf_protect(_rinterface.rlib.Rf_install(key.encode('ASCII')))
        cdata_copy = _rinterface.rlib.Rf_protect(
            _rinterface.rlib.Rf_duplicate(value.__sexp__._cdata)
        )
        res = _rinterface.rlib.Rf_defineVar(sym,
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

    def __delitem__(self, obj):
        raise NotImplementedError()

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

    def __len__(self):
        return _rinterface.rlib.Rf_xlength(self.__sexp__._cdata)


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

    
    
class StrSexpVector(SexpVector):

    _R_TYPE = _rinterface.rlib.STRSXP
    _R_GET_PTR = _rinterface._STRING_PTR
    _CAST_IN = lambda x: _rinterface.rlib.Rf_mkChar(str(x).encode('ASCII'))

    def __getitem__(self, i):
        i_c = _rinterface._python_index_to_c(self.__sexp__._cdata, i)
        res_b = _rinterface.ffi.string(
            _rinterface._STRING_VALUE(
                _rinterface.rlib.STRING_ELT(self.__sexp__._cdata, i_c)
            )
        )
        return res_b.decode('ASCII')

    def __setitem__(self, i, value):
        i_c = _rinterface._python_index_to_c(self.__sexp__._cdata, i)
        value_b = str(value).encode('ASCII')
        _rinterface._string_setitem(
            self.__sexp__._cdata, i_c,
            _rinterface.rlib.Rf_mkChar(value_b)
        )


# TODO: Make this function created once at module level
#   (after object protection from GC is added).
def _geterrmessage():
    # TODO: use isStrinb and installTrChar
    name_b = 'geterrmessage'.encode('ASCII')
    geterrmessage = _rinterface.rlib.Rf_findVar(
        _rinterface.rlib.Rf_install(_rinterface.ffi.new('char[]',
                                                        name_b)),
        globalenv.__sexp__._cdata)
    call_r = _rinterface._build_rcall(geterrmessage)
    res = _rinterface.rlib.Rf_eval(call_r, globalenv.__sexp__._cdata)
    return _rinterface._string_getitem(res, 0)
    

class RRuntimeError(Exception):
    pass


class SexpClosure(Sexp):
    
    @_cdata_to_rinterface
    def __call__(self, *args, **kwargs):
        error_occured = _rinterface.ffi.new('int *', 0)
        call_r = _rinterface._build_rcall(self.__sexp__._cdata, *args, **kwargs)
        res = _rinterface.rlib.R_tryEval(call_r,
                                         globalenv.__sexp__._cdata,
                                         error_occured)
        if error_occured[0]:
            raise RRuntimeError(_geterrmessage())
        return res


def consoleFlush():
    sys.stdout.flush()

#set_flushconsole(consoleFlush)


def consoleRead(prompt):
    text = input(prompt)
    text += "\n"
    return text


#set_readconsole(consoleRead)


def consoleMessage(x):
    sys.stdout.write(x)

#set_showmessage(consoleMessage)


# TODO: Only use rinterface-level ?
_R_RPY2_MAP = {
    _rinterface.rlib.ENVSXP: SexpEnvironment,
    _rinterface.rlib.LGLSXP: BoolSexpVector,
    _rinterface.rlib.INTSXP: IntSexpVector,
    _rinterface.rlib.REALSXP: FloatSexpVector,
    _rinterface.rlib.STRSXP: StrSexpVector,
    _rinterface.rlib.CLOSXP: SexpClosure,
    _rinterface.rlib.BUILTINSXP: SexpClosure
    }

    
baseenv = None
globalenv = None
NULL = None


def initr():
    status = embedded._initr()
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
