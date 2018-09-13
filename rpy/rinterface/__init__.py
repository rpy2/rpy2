import collections
import enum
import math
import os
import sys
import warnings
from . import _rinterface_capi as _rinterface
from . import embedded
from . import conversion


class RTYPES(enum.IntEnum):
    """Native R types, as defined in R's C API."""
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


_cdata_res_to_rinterface = conversion._cdata_res_to_rinterface
_evaluated_promise = _rinterface._evaluated_promise
R_NilValue = _rinterface.rlib.R_NilValue


@_cdata_res_to_rinterface
def parse(text, num=-1):
    """
    :param:`text` A string with R code to parse.
    :param:`num` The maximum number of lines to parse. If -1, no
      limit is applied.
    """
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


class _MissingArgType(object):

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
    @_cdata_res_to_rinterface
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

    @_cdata_res_to_rinterface
    def list_attrs(self):
        return _rinterface._list_attrs(self.__sexp__._cdata)

    @_cdata_res_to_rinterface
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

    @property
    @_cdata_res_to_rinterface
    def names(self):
        return _rinterface.rlib.Rf_getAttrib(
            self.__sexp__._cdata,
            _rinterface.rlib.R_NameSymbol)


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

    @_cdata_res_to_rinterface
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

    @_cdata_res_to_rinterface
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

    @_cdata_res_to_rinterface
    def frame(self):
        # TODO: move body to _rinterface-level function
        return self.__sexp__._cdata.u.envsxp.frame

    @_cdata_res_to_rinterface
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

    @_cdata_res_to_rinterface
    def eval(self, env=None):
        if not env:
            env = globalenv
        return _rinterface.rlib.Rf_eval(self.__sexp__._cdata, env)


# TODO: move to _rinterface-level function (as ABI / API compatibility
# will have API-defined code compile for efficiency).
def _populate_r_vector(iterable, r_vector, set_elt, cast_value):
    for i, v in enumerate(iterable):
        set_elt(r_vector, i, cast_value(v))


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
    @_cdata_res_to_rinterface
    def from_iterable(cls, iterable, cast_in=None):
        if cast_in is None:
            cast_in = cls._CAST_IN
        n = len(iterable)
        r_vector = _rinterface.rlib.Rf_protect(
            _rinterface.rlib.Rf_allocVector(
                cls._R_TYPE, n)
        )
        try:
            _populate_r_vector(iterable,
                               r_vector,
                               cls._R_SET_ELT,
                               cast_in)
        finally:
            _rinterface.rlib.Rf_unprotect(1)
        return r_vector

    def __getitem__(self, i):
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            res = conversion._cdata_to_rinterface(
                _rinterface.rlib.VECTOR_ELT(cdata, i_c))
        elif isinstance(i, slice):
            res = type(self).from_iterable(
                [_rinterface.rlib.VECTOR_ELT(cdata, i_c) for i_c in range(*i.indices(len(self)))],
                cast_in = lambda x: x
            )
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))
        return res
    
    def __setitem__(self, i, value):
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            _rinterface.rlib.SET_VECTOR_ELT(cdata, i_c,
                                            value.__sexp__._cdata)
        elif isinstance(i, slice):
            for i_c, v in zip(range(*i.indices(len(self))), value):
                _rinterface.rlib.SET_VECTOR_ELT(cdata, i_c,
                                                v.__sexp__._cdata)
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))

    def __len__(self):
        return _rinterface.rlib.Rf_xlength(self.__sexp__._cdata)

    def index(self, item):
        for i, e in enumerate(self):
            if e == item:
                return i
        raise ValueError("'%s' is not in R vector" % item)


def _cast_in_byte(x):
    if isinstance(x, int):
        if x > 255:
            raise ValueError('byte must be in range(0, 256)')
    elif isinstance(x, (bytes, bytearray)):
        if len(x) != 1:
            raise ValueError('byte must be a single character')
        x = ord(x)
    else:
        raise ValueError('byte must be an integer [0, 255] or a single byte character')
    return x


class ByteSexpVector(SexpVector):

    _R_TYPE = _rinterface.rlib.RAWSXP
    _R_SET_ELT = lambda x, i, v: _rinterface._RAW(x).__setitem__(i, v)
    _CAST_IN = _cast_in_byte
    
    def __getitem__(self, i):
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            res = _rinterface.rlib.RAW_ELT(cdata, i_c)
        elif isinstance(i, slice):
            res = type(self).from_iterable(
                [_rinterface.rlib.RAW_ELT(cdata, i_c) for i_c in range(*i.indices(len(self)))]
            )
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))
        return res

    def __setitem__(self, i, value):
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            _rinterface.rlib.RAW(cdata)[i_c] = _cast_in_byte(value)
        elif isinstance(i, slice):
            for i_c, v in zip(range(*i.indices(len(self))), value):
                if v > 255:
                    raise ValueError('byte must be in range(0, 256)')
                _rinterface.rlib.RAW(cdata)[i_c] = _cast_in_byte(v)
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))


class BoolSexpVector(SexpVector):
    
    _R_TYPE = _rinterface.rlib.LGLSXP
    _R_SET_ELT = _rinterface.rlib.SET_LOGICAL_ELT
    _R_GET_PTR = _rinterface._LOGICAL
    _CAST_IN = bool

    def __getitem__(self, i):
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            res = bool(_rinterface.rlib.LOGICAL_ELT(cdata, i_c))
        elif isinstance(i, slice):
            res = type(self).from_iterable(
                [_rinterface.rlib.LOGICAL_ELT(cdata, i_c) for i_c in range(*i.indices(len(self)))]
            )
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))
        return res

    def __setitem__(self, i, value):
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            _rinterface.rlib.SET_LOGICAL_ELT(cdata, i_c,
                                             int(value))
        elif isinstance(i, slice):
            for i_c, v in zip(range(*i.indices(len(self))), value):
                _rinterface.rlib.SET_LOGICAL_ELT(cdata, i_c,
                                                 int(v))
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))


class IntSexpVector(SexpVector):

    _R_TYPE = _rinterface.rlib.INTSXP
    _R_SET_ELT = _rinterface.rlib.SET_INTEGER_ELT
    _CAST_IN = int
    
    def __getitem__(self, i):
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            res = _rinterface.rlib.INTEGER_ELT(cdata, i_c)
        elif isinstance(i, slice):
            res = type(self).from_iterable(
                [_rinterface.rlib.INTEGER_ELT(cdata, i_c) for i_c in range(*i.indices(len(self)))]
            )
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))
        return res

    def __setitem__(self, i, value):
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            _rinterface.rlib.SET_INTEGER_ELT(cdata, i_c,
                                             int(value))
        elif isinstance(i, slice):
            for i_c, v in zip(range(*i.indices(len(self))), value):
                _rinterface.rlib.SET_INTEGER_ELT(cdata, i_c,
                                                 int(v))
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))
        

class FloatSexpVector(SexpVector):

    _R_TYPE = _rinterface.rlib.REALSXP
    _R_SET_ELT = _rinterface.rlib.SET_REAL_ELT
    _CAST_IN = float

    def __getitem__(self, i):
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            res = _rinterface.rlib.REAL_ELT(cdata, i_c)
        elif isinstance(i, slice):
            res = type(self).from_iterable(
                [_rinterface.rlib.REAL_ELT(cdata, i_c) for i_c in range(*i.indices(len(self)))]
            )
        else:
            raise TypeError('Indices must be integers or slices, not %s' % type(i))
        return res

    def __setitem__(self, i, value):
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            _rinterface.rlib.SET_REAL_ELT(cdata, i_c,
                                          float(value))
        elif isinstance(i, slice):
            for i_c, v in zip(range(*i.indices(len(self))), value):
                _rinterface.rlib.SET_REAL_ELT(cdata, i_c,
                                              float(v))
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))


class ComplexSexpVector(SexpVector):

    _R_TYPE = _rinterface.rlib.CPLXSXP
    _R_SET_ELT = lambda x, i, v: _rinterface._COMPLEX(x).__setitem__(i, v)
    _CAST_IN = lambda x: (x.real, x.imag) if isinstance(x, complex) else x

    def __getitem__(self, i):
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            _ = _rinterface.rlib.COMPLEX_ELT(cdata, i_c)
            res = complex(_.r, _.i)
        elif isinstance(i, slice):
            res = type(self).from_iterable(
                [_rinterface.rlib.COMPLEX_ELT(cdata, i_c) for i_c in range(*i.indices(len(self)))]
            )
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))
        return res

    def __setitem__(self, i, value):
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            _ = complex(value)
            _rinterface._COMPLEX(cdata)[i_c] = (_.real, _.imag)
        elif isinstance(i, slice):
            for i_c, v in zip(range(*i.indices(len(self))), value):
                _ = complex(v)
                _rinterface._COMPLEX(cdata)[i_c] = (_.real, _.imag)
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))

                
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
    _R_SET_ELT = _rinterface.rlib.SET_STRING_ELT
    _CAST_IN = lambda x: x.__sexp__._cdata if isinstance(x, CharSexp) else _rinterface._str_to_charsxp(x)

    def __getitem__(self, i):
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            res = _rinterface._string_getitem(cdata, i_c)
        elif isinstance(i, slice):
            res = type(self).from_iterable(
                [_rinterface._string_getitem(cdata, i_c) for i_c in range(*i.indices(len(self)))]
            )
        else:
            raise TypeError('Indices must be integers or slices, not %s' % type(i))
        return res

    def __setitem__(self, i, value):
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            self._R_SET_ELT(
                cdata, i_c,
                _rinterface._str_to_charsxp(value)
            )
        elif isinstance(i, slice):
            for i_c, v in zip(range(*i.indices(len(self))), value):
                self._R_SET_ELT(
                    cdata, i_c,
                    _rinterface._str_to_charsxp(v)
                )
        else:
            raise TypeError('Indices must be integers or slices, not %s' % type(i))

    def get_charsxp(self, i):
        i_c = _rinterface._python_index_to_c(self.__sexp__._cdata, i)
        return CharSexp(
            _rinterface.SexpCapsule(
                _rinterface.rlib.STRING_ELT(self.__sexp__._cdata, i_c)
            )
        )


class ListSexpVector(SexpVector):
    _R_TYPE = _rinterface.rlib.VECSXP
    _R_SET_ELT = _rinterface.rlib.SET_VECTOR_ELT
    _CAST_IN = lambda x: x.__sexp__._cdata


class PairlistSexpVector(SexpVector):
    _R_TYPE = _rinterface.rlib.LISTSXP
    _R_SET_ELT = _rinterface.rlib.SET_VECTOR_ELT
    _CAST_IN = lambda x: x.__sexp__._cdata

    def __getitem__(self, i):
        cdata = self.__sexp__._cdata
        rlib = _rinterface.rlib
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            item_cdata = rlib.Rf_nthcdr(cdata, i_c)
            protect_count = 0
            try:
                res_cdata = rlib.Rf_protect(rlib.Rf_allocVector(RTYPES.VECSXP, 1))
                protect_count += 1
                rlib.SET_VECTOR_ELT(
                    res_cdata,
                    0,
                    rlib.CAR(
                        item_cdata
                    ))
                res_name = rlib.Rf_protect(rlib.Rf_allocVector(RTYPES.STRSXP, 1))
                protect_count += 1
                rlib.SET_STRING_ELT(
                    res_name,
                    0,
                    rlib.PRINTNAME(rlib.TAG(item_cdata)))
                rlib.Rf_setAttrib(res_cdata, rlib.R_NameSymbol, res_name)
                res = conversion._cdata_to_rinterface(res_cdata)
            finally:
                rlib.Rf_unprotect(protect_count)            
        elif isinstance(i, slice):
            iter_indices = range(*i.indices(len(self)))
            n = len(iter_indices)
            res_cdata = rlib.Rf_protect(
                rlib.Rf_allocVector(
                    self._R_TYPE, n)
            )
            iter_res_cdata = res_cdata
            try:
                set_elt = self._R_SET_ELT
                i_self = 0
                lst_cdata = self.__sexp__._cdata
                for i in iter_indices :
                    while i_self < i:
                        if i_self > len(self):
                            raise IndexError('index out of range')
                        lst_cdata = rlib.CDR(lst_cdata)
                        i_self += 1
                    rlib.SETCAR(iter_res_cdata,
                                rlib.CAR(lst_cdata))
                    rlib.SET_TAG(iter_res_cdata,
                                 rlib.TAG(lst_cdata))
                    res_cdata = rlib.CDR(iter_res_cdata)
                res = conversion._cdata_to_rinterface(iter_res_cdata)
            finally:
                rlib.Rf_unprotect(1)
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))
        return res

    @classmethod
    @_cdata_res_to_rinterface
    def from_iterable(cls, iterable, cast_in=None):
        raise NotImplementedError()

class ExprSexpVector(SexpVector):
    _R_TYPE = _rinterface.rlib.EXPRSXP
    _R_GET_PTR = None
    _CAST_IN = None


class LangSexpVector(SexpVector):
    _R_TYPE = _rinterface.rlib.LANGSXP
    _R_GET_PTR = None
    _CAST_IN = None

    @_cdata_res_to_rinterface
    def __getitem__(self, i):
        cdata = self.__sexp__._cdata
        i_c = _rinterface._python_index_to_c(cdata, i)
        return _rinterface.rlib.CAR(
            _rinterface.rlib.Rf_nthcdr(cdata, i_c)
        )

    def __setitem__(self, i, value):
        cdata = self.__sexp__._cdata
        i_c = _rinterface._python_index_to_c(cdata, i)
        _rinterface.rlib.SETCAR(
            _rinterface.rlib.Rf_nthcdr(cdata, i_c),
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
    
    @_cdata_res_to_rinterface
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

    @_cdata_res_to_rinterface
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
    @_cdata_res_to_rinterface
    def closureenv(self):
        return _rinterface.rlib.CLOENV(self.__sexp__._cdata)


class SexpS4(Sexp):
    pass

# TODO: clean up
def make_extptr(obj, tag, protected):
    if protected is None:
        cdata_protected = _rinterface.rlib.R_NilValue
    else:
        try:
            cdata_protected = protected.__sexp__._cdata
        except AttributeError:
            raise TypeError('Argument protected must inherit from Sexp')
            
    ptr = _rinterface.ffi.new_handle(obj)
    cdata = _rinterface.rlib.Rf_protect(
        _rinterface.rlib.R_MakeExternalPtr(
            ptr,
            tag,
            cdata_protected))
    _rinterface.rlib.R_RegisterCFinalizer(
        cdata,
        _rinterface._capsule_finalizer)
    res = _rinterface.SexpCapsuleWithPassenger(cdata, obj, ptr)
    _rinterface.rlib.Rf_unprotect(1)
    return res


class SexpExtPtr(Sexp):

    TYPE_TAG = 'Python'

    @classmethod
    def from_pyobject(cls, func, tag=TYPE_TAG,
                      protected=None):
        scaps = make_extptr(func,
                            _rinterface._str_to_charsxp(cls.TYPE_TAG),
                            protected)
        res = cls(scaps)
        if tag != cls.TYPE_TAG:
            res.TYPE_TAG = tag
        return res


# TODO: Only use rinterface-level ?
conversion._R_RPY2_MAP.update({
    _rinterface.rlib.EXPRSXP: ExprSexpVector,
    _rinterface.rlib.LANGSXP: LangSexpVector,
    _rinterface.rlib.ENVSXP: SexpEnvironment,
    _rinterface.rlib.RAWSXP: ByteSexpVector,
    _rinterface.rlib.LGLSXP: BoolSexpVector,
    _rinterface.rlib.INTSXP: IntSexpVector,
    _rinterface.rlib.REALSXP: FloatSexpVector,
    _rinterface.rlib.CPLXSXP: ComplexSexpVector,
    _rinterface.rlib.STRSXP: StrSexpVector,
    _rinterface.rlib.VECSXP: ListSexpVector,
    _rinterface.rlib.LISTSXP: PairlistSexpVector,
    _rinterface.rlib.CLOSXP: SexpClosure,
    _rinterface.rlib.BUILTINSXP: SexpClosure,
    _rinterface.rlib.SPECIALSXP: SexpClosure,
    _rinterface.rlib.EXTPTRSXP: SexpExtPtr,
    _rinterface.rlib.SYMSXP: SexpSymbol,
    _rinterface.rlib.S4SXP: SexpS4
    })
conversion._R_RPY2_DEFAULT_MAP = Sexp

conversion._PY_RPY2_MAP.update({
    int: _rinterface._int_to_sexp,
    float: _rinterface._float_to_sexp
    })


def vector(iterable, rtype):
    error = False
    try:
        cls = conversion._R_RPY2_MAP[rtype]
    except KeyError:
        error = True
    if not error and not issubclass(cls, SexpVector):
        error = True
    if error:
        raise ValueError(
            'Unable to build a vector from type "%s"' % RTYPES(rtype))
    return cls.from_iterable(iterable)


class RRuntimeWarning(RuntimeWarning):
    pass


baseenv = None
globalenv = None
emptyenv = None
NULL = None
MissingArg = None
NA_Character = None
NA_Integer = _rinterface.rlib.R_NaInt
NA_Logical = _rinterface.rlib.R_NaInt
NA_Real = _rinterface.rlib.R_NaReal
NA_Complex = _rinterface.ffi.new('Rcomplex *',
                                 [NA_Real, NA_Real])
                                              
def initr():
    status = embedded._initr()
    _rinterface._register_external_symbols()
    _post_initr_setup()
    return status


def _post_initr_setup():

    global emptyenv
    emptyenv = SexpEnvironment(
        _rinterface.SexpCapsule(_rinterface.rlib.R_EmptyEnv)
    )

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

    global MissingArg
    MissingArg = _MissingArgType()

    global NA_Character
    NA_Character = CharSexp(
        _rinterface.SexpCapsule(_rinterface.rlib.R_NaString)
    )


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
    rpy_fun = SexpExtPtr.from_pyobject(function)
    # TODO: this is a hack. Find a better way.
    template = parse("""
      function(...) { .External(".Python", foo, ...);
    }
    """)
    template[0][2][1][2] = rpy_fun
    # TODO: use lower-level eval ?
    res = baseenv['eval'](template)
    # TODO: hack to prevent the nested function from having its
    #   refcount down to zero when returning
    res.__nested_sexp__ = rpy_fun.__sexp__
    return res

    
