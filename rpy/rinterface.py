import atexit
import enum
import typing
import rpy2.rinterface_lib._rinterface_capi as _rinterface
import rpy2.rinterface_lib.callbacks as callbacks
import rpy2.rinterface_lib.embedded as embedded
import rpy2.rinterface_lib.conversion as conversion
import rpy2.rinterface_lib.memorymanagement as memorymanagement
import rpy2.rinterface_lib.na_values as na_values
import rpy2.rinterface_lib.bufferprotocol as bufferprotocol
import rpy2.rinterface_lib.sexp as sexp


Sexp = sexp.Sexp
StrSexpVector = sexp.StrSexpVector
CharSexp = sexp.CharSexp
SexpVector = sexp.SexpVector
RTYPES = sexp.RTYPES

unserialize = sexp.unserialize

_cdata_res_to_rinterface = conversion._cdata_res_to_rinterface
_evaluated_promise = _rinterface._evaluated_promise
R_NilValue = _rinterface.rlib.R_NilValue
RRuntimeError = _rinterface.RRuntimeError

endr = embedded.endr

@_cdata_res_to_rinterface
def parse(text: str, num: int = -1):
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
                'with that is an instance of rpy2.rinterface.sexp.Sexp '
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
    def get(self,
            key: str,
            wantfun: int = False):
        # TODO: move check of R_UnboundValue to _rinterface ?
        if not (isinstance(key, str) and len(key)):
            raise ValueError('The key must be a non-empty string.')
        with memorymanagement.rmemory() as rmemory:
            symbol = rmemory.protect(
                _rinterface.rlib.Rf_install(_rinterface._str_to_cchar(key))
            )
            if wantfun:
                res = _rinterface._findfun(symbol, self.__sexp__._cdata)
            else:
                res = _rinterface._findvar(symbol, self.__sexp__._cdata)
        if res == _rinterface.rlib.R_UnboundValue:
            raise KeyError("'%s' not found" % key)
        return res

    @_cdata_res_to_rinterface
    @_evaluated_promise
    def __getitem__(self, key: str) -> typing.Any:
        # TODO: move check of R_UnboundValue to _rinterface
        if not (isinstance(key, str) and len(key)):
            raise ValueError('The key must be a non-empty string.')
        with memorymanagement.rmemory() as rmemory:
            symbol = rmemory.protect(
                _rinterface.rlib.Rf_install(_rinterface._str_to_cchar(key))
            )
            res = _rinterface._findVarInFrame(symbol, self.__sexp__._cdata)
        if res == _rinterface.rlib.R_UnboundValue:
            raise KeyError("'%s' not found" % key)
        return res

    def __setitem__(self, key: str, value) -> None:
        # TODO: move body to _rinterface-level function
        if not (isinstance(key, str) and len(key)):
            raise ValueError('The key must be a non-empty string.')
        if (self.__sexp__._cdata == _rinterface.rlib.R_BaseEnv) or \
           (self.__sexp__._cdata == _rinterface.rlib.R_EmptyEnv):
            raise ValueError('Cannot remove variables from the base or '
                             'empty environments.')
        # TODO: call to Rf_duplicate needed ?
        with memorymanagement.rmemory() as rmemory:
            symbol = rmemory.protect(
                _rinterface.rlib.Rf_install(_rinterface._str_to_cchar(key))
            )
            cdata = rmemory.protect(_rinterface._get_cdata(value))
            cdata_copy = rmemory.protect(
                _rinterface.rlib.Rf_duplicate(cdata)
            )
            res = _rinterface.rlib.Rf_defineVar(symbol,
                                                cdata_copy,
                                                self.__sexp__._cdata)

    def __len__(self) -> int:
        with memorymanagement.rmemory() as rmemory:
            symbols = rmemory.protect(
                _rinterface.rlib.R_lsInternal(self.__sexp__._cdata,
                                              _rinterface.rlib.TRUE)
            )
            n = _rinterface.rlib.Rf_xlength(symbols)
        return n

    def __delitem__(self, key: str):
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

        with memorymanagement.rmemory() as rmemory:
            key_cdata = rmemory.protect(
                _rinterface.rlib.Rf_mkString(_rinterface._str_to_cchar(key))
            )
            res_rm = _rinterface._remove(key_cdata, 
			                 self.__sexp__._cdata, 
			                 _rinterface.rlib.Rf_ScalarLogical(
                                            _rinterface.rlib.FALSE))

    @_cdata_res_to_rinterface
    def frame(self):
        return _rinterface.rlib.FRAME(self.__sexp__._cdata)

    @property
    @_cdata_res_to_rinterface
    def enclos(self):
        return _rinterface.rlib.ENCLOS(self.__sexp__._cdata)

    @enclos.setter
    def enclos(self, value: 'SexpEnvironment'):
        assert isinstance(value, SexpEnvironment)
        _rinterface.rlib.SET_ENCLOS(self.__sexp__._cdata,
                                    value.__sexp__.cdata)
    
    def keys(self):
        with memorymanagement.rmemory() as rmemory:
            symbols = rmemory.protect(
                _rinterface.rlib.R_lsInternal(self.__sexp__._cdata,
                                              _rinterface.rlib.TRUE)
            )
            n = _rinterface.rlib.Rf_xlength(symbols)
            res = []
            for i in range(n):
                res.append(_rinterface._string_getitem(symbols, i))
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
            env = embedded.globalenv
        return _rinterface.rlib.Rf_eval(self.__sexp__._cdata, env)


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
    
    def __getitem__(self, i: int) -> typing.Union[int, 'ByteSexpVector']:
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

    def __setitem__(self, i: int, value):
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
    _R_SET_ELT = _rinterface.SET_LOGICAL_ELT
    _R_GET_PTR = _rinterface._LOGICAL
    _CAST_IN = lambda x: NA_Logical if x is None or x == _rinterface.rlib.R_NaInt else bool(x)

    def __getitem__(self, i: int) -> typing.Union[typing.Optional[bool],
                                                  'BoolSexpVector']:
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            elt = _rinterface.rlib.LOGICAL_ELT(cdata, i_c)
            res = None if elt == NA_Logical else bool(elt)
        elif isinstance(i, slice):
            res = type(self).from_iterable(
                [_rinterface.rlib.LOGICAL_ELT(cdata, i_c)
                 for i_c in range(*i.indices(len(self)))]
            )
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))
        return res

    def __setitem__(self, i: int, value):
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            _rinterface.rlib.LOGICAL_ELT(cdata, i_c,
                                             int(value))
        elif isinstance(i, slice):
            for i_c, v in zip(range(*i.indices(len(self))), value):
                _rinterface.SET_LOGICAL_ELT(cdata, i_c,
                                            int(v))
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))

    def memoryview(self):
        b = _rinterface.ffi.buffer(
            _rinterface._LOGICAL(self.__sexp__._cdata),
            _rinterface.ffi.sizeof('int') * len(self))
        shape = bufferprotocol.getshape(self.__sexp__._cdata)
        mv = memoryview(b).cast('i', shape)
        return mv


class IntSexpVector(SexpVector):

    _R_TYPE = _rinterface.rlib.INTSXP
    _R_SET_ELT = _rinterface.SET_INTEGER_ELT
    _CAST_IN = int
    
    def __getitem__(self, i: int) -> typing.Union[int, 'IntSexpVector']:
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

    def __setitem__(self, i: int, value):
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            _rinterface.SET_INTEGER_ELT(cdata, i_c,
                                        int(value))
        elif isinstance(i, slice):
            for i_c, v in zip(range(*i.indices(len(self))), value):
                _rinterface.SET_INTEGER_ELT(cdata, i_c,
                                            int(v))
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))

    def memoryview(self) -> memoryview:
        b = _rinterface.ffi.buffer(
            _rinterface._INTEGER(self.__sexp__._cdata),
            _rinterface.ffi.sizeof('int') * len(self))
        shape = bufferprotocol.getshape(self.__sexp__._cdata)
        mv = memoryview(b).cast('i', shape)
        return mv


class FloatSexpVector(SexpVector):

    _R_TYPE = _rinterface.rlib.REALSXP
    _R_SET_ELT = _rinterface.SET_REAL_ELT
    _CAST_IN = float

    def __getitem__(self, i: int) -> typing.Union[float, 'FloatSexpVector']:
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

    def __setitem__(self, i: int, value):
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            _rinterface.SET_REAL_ELT(cdata, i_c,
                                     float(value))
        elif isinstance(i, slice):
            for i_c, v in zip(range(*i.indices(len(self))), value):
                _rinterface.SET_REAL_ELT(cdata, i_c,
                                         float(v))
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))

    def memoryview(self):
        b = _rinterface.ffi.buffer(
            _rinterface._REAL(self.__sexp__._cdata),
            _rinterface.ffi.sizeof('double') * len(self))
        shape = bufferprotocol.getshape(self.__sexp__._cdata)
        mv = memoryview(b).cast('d', shape)
        return mv


class ComplexSexpVector(SexpVector):

    _R_TYPE = _rinterface.rlib.CPLXSXP
    _R_SET_ELT = lambda x, i, v: _rinterface._COMPLEX(x).__setitem__(i, v)
    _CAST_IN = lambda x: (x.real, x.imag) if isinstance(x, complex) else x

    def __getitem__(self, i: int) -> typing.Union[complex, 'ComplexSexpVector']:
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

    def __setitem__(self, i: int, value):
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
        

class ListSexpVector(SexpVector):
    _R_TYPE = _rinterface.rlib.VECSXP
    _R_SET_ELT = _rinterface.rlib.SET_VECTOR_ELT
    _CAST_IN = _rinterface._get_cdata


class PairlistSexpVector(SexpVector):
    _R_TYPE = _rinterface.rlib.LISTSXP
    _R_SET_ELT = _rinterface.rlib.SET_VECTOR_ELT
    _CAST_IN = _rinterface._get_cdata

    def __getitem__(self, i: int):
        cdata = self.__sexp__._cdata
        rlib = _rinterface.rlib
        if isinstance(i, int):
            # R-exts says that it is converted to a VECSXP when subsetted.
            i_c = _rinterface._python_index_to_c(cdata, i)
            item_cdata = rlib.Rf_nthcdr(cdata, i_c)
            with memorymanagement.rmemory() as rmemory:
                res_cdata = rmemory.protect(
                    rlib.Rf_allocVector(RTYPES.VECSXP, 1))
                rlib.SET_VECTOR_ELT(
                    res_cdata,
                    0,
                    rlib.CAR(
                        item_cdata
                    ))
                res_name = rmemory.protect(
                    rlib.Rf_allocVector(RTYPES.STRSXP, 1))
                rlib.SET_STRING_ELT(
                    res_name,
                    0,
                    rlib.PRINTNAME(rlib.TAG(item_cdata)))
                rlib.Rf_namesgets(res_cdata, res_name)
                res = conversion._cdata_to_rinterface(res_cdata)
        elif isinstance(i, slice):
            iter_indices = range(*i.indices(len(self)))
            n = len(iter_indices)
            with memorymanagement.rmemory() as rmemory:
                res_cdata = rmemory.protect(
                    rlib.Rf_allocVector(
                        self._R_TYPE, n)
                )
                iter_res_cdata = res_cdata
                set_elt = self._R_SET_ELT
                prev_i = 0
                lst_cdata = self.__sexp__._cdata
                for i in iter_indices :
                    if i >= len(self):
                        raise IndexError('index out of range')
                    lst_cdata = rlib.Rf_nthcdr(lst_cdata, i - prev_i)
                    prev_i = i
                    rlib.SETCAR(iter_res_cdata,
                                rlib.CAR(lst_cdata))
                    rlib.SET_TAG(iter_res_cdata,
                                 rlib.TAG(lst_cdata))
                    iter_res_cdata = rlib.CDR(iter_res_cdata)
                res = conversion._cdata_to_rinterface(res_cdata)
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
    def __getitem__(self, i: int):
        cdata = self.__sexp__._cdata
        i_c = _rinterface._python_index_to_c(cdata, i)
        return _rinterface.rlib.CAR(
            _rinterface.rlib.Rf_nthcdr(cdata, i_c)
        )

    def __setitem__(self, i: int, value):
        cdata = self.__sexp__._cdata
        i_c = _rinterface._python_index_to_c(cdata, i)
        _rinterface.rlib.SETCAR(
            _rinterface.rlib.Rf_nthcdr(cdata, i_c),
            value.__sexp__._cdata
        )
    

class SexpClosure(Sexp):
    
    @_cdata_res_to_rinterface
    def __call__(self, *args, **kwargs):
        error_occured = _rinterface.ffi.new('int *', 0)
        with memorymanagement.rmemory() as rmemory:
            call_r = rmemory.protect(
                _rinterface.build_rcall(self.__sexp__._cdata, args,
                                        kwargs.items()))
            res = rmemory.protect(
                _rinterface.rlib.R_tryEval(
                    call_r,
                    embedded.globalenv.__sexp__._cdata,
                    error_occured))
            if error_occured[0]:
                raise _rinterface.RRuntimeError(_rinterface._geterrmessage())
        return res

    @_cdata_res_to_rinterface
    def rcall(self, keyvals, environment):
        # TODO: check keyvals are pairs ?
        assert isinstance(environment, SexpEnvironment)
        error_occured = _rinterface.ffi.new('int *', 0)
        with memorymanagement.rmemory() as rmemory:
            call_r = rmemory.protect(
                _rinterface.build_rcall(self.__sexp__._cdata, [],
                                        keyvals))
            res = rmemory.protect(
                _rinterface.rlib.R_tryEval(call_r,
                                           environment.__sexp__._cdata,
                                           error_occured))
            if error_occured[0]:
                raise _rinterface.RRuntimeError(_rinterface._geterrmessage())
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
            raise TypeError('Argument protected must inherit from %s' % type(Sexp))
            
    ptr = _rinterface.ffi.new_handle(obj)
    with memorymanagement.rmemory() as rmemory:
        cdata = rmemory.protect(
            _rinterface.rlib.R_MakeExternalPtr(
                ptr,
                tag,
                cdata_protected))
        _rinterface.rlib.R_RegisterCFinalizer(
            cdata,
            _rinterface._capsule_finalizer)
        res = _rinterface.SexpCapsuleWithPassenger(cdata, obj, ptr)
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


def vector(iterable, rtype: RTYPES):
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

emptyenv = None
baseenv = None
globalenv = None
NULL = None
MissingArg = None
NA_Character = None
NA_Integer = None
NA_Logical = None
NA_Real = None
NA_Complex = None
                                              
def initr() -> None:
    status = embedded._initr()
    atexit.register(endr, 0)
    _rinterface._register_external_symbols()
    _post_initr_setup()
    return status


def _post_initr_setup():

    embedded.emptyenv = SexpEnvironment(
        _rinterface.SexpCapsule(_rinterface.rlib.R_EmptyEnv)
    )
    global emptyenv
    emptyenv = embedded.emptyenv

    embedded.baseenv = SexpEnvironment(
        _rinterface.SexpCapsule(_rinterface.rlib.R_BaseEnv)
    )
    global baseenv
    baseenv = embedded.baseenv


    embedded.globalenv = SexpEnvironment(
        _rinterface.SexpCapsule(_rinterface.rlib.R_GlobalEnv)
    )
    global globalenv
    globalenv = embedded.globalenv


    global NULL    
    NULL = _NULL()

    global MissingArg
    MissingArg = _MissingArgType()

    global NA_Character
    na_values.NA_Character = CharSexp(
        _rinterface.SexpCapsule(_rinterface.rlib.R_NaString)
    )
    NA_Character = na_values.NA_Character

    global NA_Integer
    na_values.NA_Integer = na_values.NAIntegerType(_rinterface.rlib.R_NaInt)
    NA_Integer = na_values.NA_Integer

    global NA_Logical
    na_values.NA_Logical = na_values.NALogicalType(_rinterface.rlib.R_NaInt)
    NA_Logical = na_values.NA_Logical

    global NA_Real
    na_values.NA_Real = na_values.NARealType(_rinterface.rlib.R_NaReal)
    NA_Real = na_values.NA_Real

    global NA_Complex
    na_values.NA_Complex = _rinterface.ffi.new(
        'Rcomplex *',
        [_rinterface.rlib.R_NaReal, _rinterface.rlib.R_NaReal])
    NA_Complex = na_values.NA_Complex


def rternalize(function: typing.Callable):
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

    
