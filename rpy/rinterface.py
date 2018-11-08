import abc
import atexit
import typing
from rpy2.rinterface_lib import openrlib
import rpy2.rinterface_lib._rinterface_capi as _rinterface
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
R_NilValue = openrlib.rlib.R_NilValue

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
    return _rinterface._parse(robj.__sexp__._cdata, num)


def evalr(source: str) -> sexp.Sexp:
    res = parse(source)
    res = baseenv['eval'](res)
    return res


class NULLType(sexp.Sexp, metaclass=na_values.Singleton):

    def __init__(self):
        embedded.assert_isready()
        super().__init__(
            sexp.Sexp(
                _rinterface.UnmanagedSexpCapsule(
                    openrlib.rlib.R_NilValue
                )
            )
        )

    def __repr__(self):
        return super().__repr__() + (' [%s]' % self.typeof)

    def __bool__(self):
        return False

    @property
    def __sexp__(self):
        return self._sexpobject

    @property
    def rid(self):
        return self._sexpobject.rid

    @property
    def typeof(self):
        return RTYPES(_rinterface._TYPEOF(self.__sexp__._cdata))


class _MissingArgType(object):

    __slots__ = ('_sexpobject', )

    def __init__(self):
        self._sexpobject = _rinterface.UnmanagedSexpCapsule(
            openrlib.rlib.R_MissingArg)

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
                openrlib.rlib.Rf_install(name_cdata))
            super().__init__(sexp)
        else:
            raise ValueError(
                'The constructor must be called '
                'with that is an instance of rpy2.rinterface.sexp.Sexp '
                'or an instance of rpy2.rinterface._rinterface.SexpCapsule')

    def __str__(self) -> str:
        return conversion._cchar_to_str(
            openrlib._STRING_VALUE(
                self._sexpobject._cdata
            )
        )


class SexpEnvironment(Sexp):
    """Proxy for an R "environment" object.

    An R "environment" object can be thought of as a mix of a
    mapping (like a `dict`) and a scope. To make it more "Pythonic",
    both aspects are kept separate and the method `__getitem__` will
    get an item as it would for a Python `dict` while the method `find`
    will get an item as if it was a scope."""

    @_cdata_res_to_rinterface
    @_evaluated_promise
    def find(self,
             key: str,
             wantfun: int = False) -> Sexp:
        """Find an item, starting with this R environment.

        Raises a `KeyError` is the key cannot be found."""
        
        if not isinstance(key, str):
            raise TypeError('The key must be a non-empty string.')
        elif not len(key):
            raise ValueError('The key must be a non-empty string.')
        with memorymanagement.rmemory() as rmemory:
            symbol = rmemory.protect(
                openrlib.rlib.Rf_install(conversion._str_to_cchar(key))
            )
            if wantfun:
                # One would expect this to be like
                #   res = _rinterface._findfun(symbol, self.__sexp__._cdata)
                # but R's findfun will segfault if the symbol is not in
                # the environment. :/
                rho = self
                while rho.rid != emptyenv.rid:
                    res = _rinterface._findVarInFrame(symbol,
                                                      rho.__sexp__._cdata)
                    if _rinterface._TYPEOF(res) in (openrlib.rlib.CLOSXP,
                                                    openrlib.rlib.BUILTINSXP):
                        break
                    # TODO: move check of R_UnboundValue to _rinterface ?
                    res = openrlib.rlib.R_UnboundValue
                    rho = rho.enclos
            else:
                res = _rinterface._findvar(symbol, self.__sexp__._cdata)
        # TODO: move check of R_UnboundValue to _rinterface ?
        if res == openrlib.rlib.R_UnboundValue:
            raise KeyError("'%s' not found" % key)
        return res

    @_cdata_res_to_rinterface
    @_evaluated_promise
    def __getitem__(self, key: str) -> typing.Any:
        if not (isinstance(key, str) and len(key)):
            raise ValueError('The key must be a non-empty string.')
        with memorymanagement.rmemory() as rmemory:
            symbol = rmemory.protect(
                openrlib.rlib.Rf_install(conversion._str_to_cchar(key))
            )
            res = _rinterface._findVarInFrame(symbol, self.__sexp__._cdata)
        # TODO: move check of R_UnboundValue to _rinterface
        if res == openrlib.rlib.R_UnboundValue:
            raise KeyError("'%s' not found" % key)
        return res

    def __setitem__(self, key: str, value) -> None:
        # TODO: move body to _rinterface-level function
        if not (isinstance(key, str) and len(key)):
            raise ValueError('The key must be a non-empty string.')
        if (self.__sexp__._cdata == openrlib.rlib.R_BaseEnv) or \
           (self.__sexp__._cdata == openrlib.rlib.R_EmptyEnv):
            raise ValueError('Cannot remove variables from the base or '
                             'empty environments.')
        # TODO: call to Rf_duplicate needed ?
        with memorymanagement.rmemory() as rmemory:
            symbol = rmemory.protect(
                openrlib.rlib.Rf_install(conversion._str_to_cchar(key))
            )
            cdata = rmemory.protect(conversion._get_cdata(value))
            cdata_copy = rmemory.protect(
                openrlib.rlib.Rf_duplicate(cdata)
            )
            openrlib.rlib.Rf_defineVar(symbol,
                                       cdata_copy,
                                       self.__sexp__._cdata)

    def __len__(self) -> int:
        with memorymanagement.rmemory() as rmemory:
            symbols = rmemory.protect(
                openrlib.rlib.R_lsInternal(self.__sexp__._cdata,
                                           openrlib.rlib.TRUE)
            )
            n = openrlib.rlib.Rf_xlength(symbols)
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
                openrlib.rlib.Rf_mkString(conversion._str_to_cchar(key))
            )
            _rinterface._remove(key_cdata,
                                self.__sexp__._cdata,
                                openrlib.rlib.Rf_ScalarLogical(
                                    openrlib.rlib.FALSE))

    @_cdata_res_to_rinterface
    def frame(self):
        """Get the parent frame of the environment."""
        return openrlib.rlib.FRAME(self.__sexp__._cdata)

    @property
    @_cdata_res_to_rinterface
    def enclos(self) -> 'SexpEnvironment':
        """Get or set the enclosing environment."""
        return openrlib.rlib.ENCLOS(self.__sexp__._cdata)

    @enclos.setter
    def enclos(self, value: 'SexpEnvironment') -> None:
        assert isinstance(value, SexpEnvironment)
        openrlib.rlib.SET_ENCLOS(self.__sexp__._cdata,
                                 value.__sexp__.cdata)

    def keys(self) -> typing.Generator[str, None, None]:
        """Generator over the keys (symbols) in the environment."""
        with memorymanagement.rmemory() as rmemory:
            symbols = rmemory.protect(
                openrlib.rlib.R_lsInternal(self.__sexp__._cdata,
                                           openrlib.rlib.TRUE)
            )
            n = openrlib.rlib.Rf_xlength(symbols)
            res = []
            for i in range(n):
                res.append(_rinterface._string_getitem(symbols, i))
        for e in res:
            yield e

    def __iter__(self) -> typing.Generator[str, None, None]:
        """See method `keys()`."""
        return self.keys()

    def is_locked(self):
        return openrlib.rlib.R_EnvironmentIsLocked(
            self.__sexp__._cdata)


class SexpPromise(Sexp):

    @_cdata_res_to_rinterface
    def eval(self, env=None):
        if not env:
            env = embedded.globalenv
        return openrlib.rlib.Rf_eval(self.__sexp__._cdata, env)


class NumpyArrayInterface(abc.ABC):
    """Numpy-specific API for accessing the content of a numpy array.

    The interface is only available / possible for some of the R vectors."""
    
    @property
    def __array_interface__(self):
        """Return an `__array_interface__` version 3.

        Note that the pointer returned in the items 'data' corresponds to
        a memory area under R's memory management and that it will become
        invalid once the area once R frees the object. It is safer to keep
        the rpy2 object proxying the R object alive for the duration the
        pointer is used in Python / numpy."""
        return {'shape': bufferprotocol.getshape(self.__sexp__._cdata),
                'typestr': self._NP_TYPESTR,
                'strides': bufferprotocol.getstrides(self.__sexp__._cdata),
                'data': self._R_GET_PTR(self.__sexp__._cdata),
                'version': 3}


def _cast_in_byte(x):
    if isinstance(x, int):
        if x > 255:
            raise ValueError('byte must be in range(0, 256)')
    elif isinstance(x, (bytes, bytearray)):
        if len(x) != 1:
            raise ValueError('byte must be a single character')
        x = ord(x)
    else:
        raise ValueError('byte must be an integer [0, 255] or a '
                         'single byte character')
    return x


def _get_raw_elt(x, i: int):
    return openrlib._RAW(x)[i]


def _set_raw_elt(x, i: int, val):
    openrlib._RAW(x)[i] = val


class ByteSexpVector(SexpVector, NumpyArrayInterface):

    _R_TYPE = openrlib.rlib.RAWSXP
    _R_GET_PTR = openrlib._RAW
    _R_VECTOR_ELT = _get_raw_elt
    _R_SET_VECTOR_ELT = _set_raw_elt
    _CAST_IN = _cast_in_byte
    _NP_TYPESTR = '|u1'

    def __getitem__(self, i: int) -> typing.Union[int, 'ByteSexpVector']:
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            res = openrlib.rlib.RAW_ELT(cdata, i_c)
        elif isinstance(i, slice):
            res = type(self).from_iterable(
                [openrlib.rlib.RAW_ELT(
                    cdata, i_c
                ) for i_c in range(*i.indices(len(self)))
                ]
            )
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))
        return res

    def __setitem__(self, i: int, value):
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            openrlib.rlib.RAW(cdata)[i_c] = _cast_in_byte(value)
        elif isinstance(i, slice):
            for i_c, v in zip(range(*i.indices(len(self))), value):
                if v > 255:
                    raise ValueError('byte must be in range(0, 256)')
                openrlib.rlib.RAW(cdata)[i_c] = _cast_in_byte(v)
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))


def _cast_in_bool(x):
    if x is None or x == openrlib.rlib.R_NaInt:
        return NA_Logical
    else:
        return bool(x)


class BoolSexpVector(SexpVector, NumpyArrayInterface):

    _R_TYPE = openrlib.rlib.LGLSXP
    _R_VECTOR_ELT = openrlib.LOGICAL_ELT
    _R_SET_VECTOR_ELT = openrlib.SET_LOGICAL_ELT
    _R_GET_PTR = openrlib._LOGICAL
    _CAST_IN = _cast_in_bool
    _NP_TYPESTR = '|i'

    def __getitem__(self, i: int) -> typing.Union[typing.Optional[bool],
                                                  'BoolSexpVector']:
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            elt = openrlib.rlib.LOGICAL_ELT(cdata, i_c)
            res = na_values.NA_Logical if elt == NA_Logical else bool(elt)
        elif isinstance(i, slice):
            res = type(self).from_iterable(
                [openrlib.rlib.LOGICAL_ELT(cdata, i_c)
                 for i_c in range(*i.indices(len(self)))]
            )
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))
        return res

    def __setitem__(self, i: int, value) -> None:
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            openrlib.rlib.SET_LOGICAL_ELT(cdata, i_c,
                                          int(value))
        elif isinstance(i, slice):
            for i_c, v in zip(range(*i.indices(len(self))), value):
                openrlib.SET_LOGICAL_ELT(cdata, i_c,
                                         int(v))
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))

    def memoryview(self):
        b = _rinterface.ffi.buffer(
            openrlib._LOGICAL(self.__sexp__._cdata),
            openrlib.ffi.sizeof('int') * len(self))
        shape = bufferprotocol.getshape(self.__sexp__._cdata)
        mv = memoryview(b).cast('i', shape)
        return mv


class IntSexpVector(SexpVector, NumpyArrayInterface):

    _R_TYPE = openrlib.rlib.INTSXP
    _R_SET_VECTOR_ELT = openrlib.SET_INTEGER_ELT
    _R_VECTOR_ELT = openrlib.INTEGER_ELT
    _R_GET_PTR = openrlib._INTEGER
    _CAST_IN = int
    _NP_TYPESTR = '|i'

    def __getitem__(self, i: int) -> typing.Union[int, 'IntSexpVector']:
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            res = openrlib.rlib.INTEGER_ELT(cdata, i_c)
            if res == na_values.NA_Integer:
                res = na_values.NA_Integer
        elif isinstance(i, slice):
            res = type(self).from_iterable(
                [openrlib.rlib.INTEGER_ELT(
                    cdata, i_c
                ) for i_c in range(*i.indices(len(self)))]
            )
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))
        return res

    def __setitem__(self, i: int, value) -> None:
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            openrlib.SET_INTEGER_ELT(cdata, i_c,
                                     int(value))
        elif isinstance(i, slice):
            for i_c, v in zip(range(*i.indices(len(self))), value):
                openrlib.SET_INTEGER_ELT(cdata, i_c,
                                         int(v))
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))

    def memoryview(self) -> memoryview:
        b = _rinterface.ffi.buffer(
            openrlib._INTEGER(self.__sexp__._cdata),
            openrlib.ffi.sizeof('int') * len(self))
        shape = bufferprotocol.getshape(self.__sexp__._cdata)
        mv = memoryview(b).cast('i', shape)
        return mv


class FloatSexpVector(SexpVector, NumpyArrayInterface):

    _R_TYPE = openrlib.rlib.REALSXP
    _R_GET_PTR = openrlib._REAL
    _R_VECTOR_ELT = openrlib.REAL_ELT
    _R_SET_VECTOR_ELT = openrlib.SET_REAL_ELT
    _CAST_IN = float
    _NP_TYPESTR = '|f'

    def __getitem__(self, i: int) -> typing.Union[float, 'FloatSexpVector']:
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            res = openrlib.rlib.REAL_ELT(cdata, i_c)
        elif isinstance(i, slice):
            res = type(self).from_iterable(
                [openrlib.rlib.REAL_ELT(
                    cdata, i_c) for i_c in range(*i.indices(len(self)))]
            )
        else:
            raise TypeError('Indices must be integers or slices, not %s' %
                            type(i))
        return res

    def __setitem__(self, i: int, value) -> None:
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            openrlib.SET_REAL_ELT(cdata, i_c,
                                  float(value))
        elif isinstance(i, slice):
            for i_c, v in zip(range(*i.indices(len(self))), value):
                openrlib.SET_REAL_ELT(cdata, i_c,
                                      float(v))
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))

    def memoryview(self) -> memoryview:
        b = _rinterface.ffi.buffer(
            openrlib._REAL(self.__sexp__._cdata),
            openrlib.ffi.sizeof('double') * len(self))
        shape = bufferprotocol.getshape(self.__sexp__._cdata)
        mv = memoryview(b).cast('d', shape)
        return mv


class ComplexSexpVector(SexpVector):

    _R_TYPE = openrlib.rlib.CPLXSXP
    _R_GET_PTR = openrlib._COMPLEX
    _R_VECTOR_ELT = lambda x, i: openrlib._COMPLEX(x)[i]
    _R_SET_VECTOR_ELT = lambda x, i, v: openrlib._COMPLEX(x).__setitem__(i, v)
    _CAST_IN = lambda x: (x.real, x.imag) if isinstance(x, complex) else x

    def __getitem__(self,
                    i: int) -> typing.Union[complex, 'ComplexSexpVector']:
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            _ = openrlib.rlib.COMPLEX_ELT(cdata, i_c)
            res = complex(_.r, _.i)
        elif isinstance(i, slice):
            res = type(self).from_iterable(
                [openrlib.rlib.COMPLEX_ELT(
                    cdata, i_c) for i_c in range(*i.indices(len(self)))]
            )
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))
        return res

    def __setitem__(self, i: int, value) -> None:
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            _ = complex(value)
            openrlib._COMPLEX(cdata)[i_c] = (_.real, _.imag)
        elif isinstance(i, slice):
            for i_c, v in zip(range(*i.indices(len(self))), value):
                _ = complex(v)
                openrlib._COMPLEX(cdata)[i_c] = (_.real, _.imag)
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))


class ListSexpVector(SexpVector):
    _R_TYPE = openrlib.rlib.VECSXP
    _R_GET_PTR = openrlib._VECTOR_PTR
    _R_VECTOR_ELT = openrlib.rlib.VECTOR_ELT
    _R_SET_VECTOR_ELT = openrlib.rlib.SET_VECTOR_ELT
    _CAST_IN = conversion._get_cdata


class PairlistSexpVector(SexpVector):
    _R_TYPE = openrlib.rlib.LISTSXP
    _R_GET_PTR = None
    _R_VECTOR_ELT = None
    _R_SET_VECTOR_ELT = None
    _CAST_IN = conversion._get_cdata

    def __getitem__(self, i: int) -> Sexp:
        cdata = self.__sexp__._cdata
        rlib = openrlib.rlib
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
                prev_i = 0
                lst_cdata = self.__sexp__._cdata
                for i in iter_indices:
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
    _R_TYPE = openrlib.rlib.EXPRSXP
    _R_GET_PTR = None
    _CAST_IN = None
    _R_VECTOR_ELT = openrlib.rlib.VECTOR_ELT
    _R_SET_VECTOR_ELT = None


class LangSexpVector(SexpVector):
    _R_TYPE = openrlib.rlib.LANGSXP
    _R_GET_PTR = None
    _CAST_IN = None
    _R_VECTOR_ELT = None
    _R_SET_VECTOR_ELT = None

    @_cdata_res_to_rinterface
    def __getitem__(self, i: int):
        cdata = self.__sexp__._cdata
        i_c = _rinterface._python_index_to_c(cdata, i)
        return openrlib.rlib.CAR(
            openrlib.rlib.Rf_nthcdr(cdata, i_c)
        )

    def __setitem__(self, i: int, value) -> None:
        cdata = self.__sexp__._cdata
        i_c = _rinterface._python_index_to_c(cdata, i)
        openrlib.rlib.SETCAR(
            openrlib.rlib.Rf_nthcdr(cdata, i_c),
            value.__sexp__._cdata
        )


class SexpClosure(Sexp):

    @_cdata_res_to_rinterface
    def __call__(self, *args, **kwargs) -> Sexp:
        error_occured = _rinterface.ffi.new('int *', 0)
        with memorymanagement.rmemory() as rmemory:
            call_r = rmemory.protect(
                _rinterface.build_rcall(self.__sexp__._cdata, args,
                                        kwargs.items()))
            res = rmemory.protect(
                openrlib.rlib.R_tryEval(
                    call_r,
                    embedded.globalenv.__sexp__._cdata,
                    error_occured))
            if error_occured[0]:
                raise embedded.RRuntimeError(_rinterface._geterrmessage())
        return res

    @_cdata_res_to_rinterface
    def rcall(self, keyvals, environment: SexpEnvironment):
        # TODO: check keyvals are pairs ?
        assert isinstance(environment, SexpEnvironment)
        error_occured = _rinterface.ffi.new('int *', 0)
        with memorymanagement.rmemory() as rmemory:
            call_r = rmemory.protect(
                _rinterface.build_rcall(self.__sexp__._cdata, [],
                                        keyvals))
            res = rmemory.protect(
                openrlib.rlib.R_tryEval(call_r,
                                        environment.__sexp__._cdata,
                                        error_occured))
            if error_occured[0]:
                raise embedded.RRuntimeError(_rinterface._geterrmessage())
        return res

    @property
    @_cdata_res_to_rinterface
    def closureenv(self) -> SexpEnvironment:
        """Closure of the R function."""
        return openrlib.rlib.CLOENV(self.__sexp__._cdata)


class SexpS4(Sexp):
    """R "S4" object."""
    pass


# TODO: clean up
def make_extptr(obj, tag, protected):
    if protected is None:
        cdata_protected = openrlib.rlib.R_NilValue
    else:
        try:
            cdata_protected = protected.__sexp__._cdata
        except AttributeError:
            raise TypeError('Argument protected must inherit from %s' %
                            type(Sexp))

    ptr = _rinterface.ffi.new_handle(obj)
    with memorymanagement.rmemory() as rmemory:
        cdata = rmemory.protect(
            openrlib.rlib.R_MakeExternalPtr(
                ptr,
                tag,
                cdata_protected))
        openrlib.rlib.R_RegisterCFinalizer(
            cdata,
            _rinterface._capsule_finalizer)
        res = _rinterface.SexpCapsuleWithPassenger(cdata, obj, ptr)
    return res


class SexpExtPtr(Sexp):

    TYPE_TAG = 'Python'

    @classmethod
    def from_pyobject(cls, func, tag: str = TYPE_TAG,
                      protected=None):
        if not isinstance(tag, str):
            raise TypeError('The tag must be a string.')
        scaps = make_extptr(func,
                            conversion._str_to_charsxp(cls.TYPE_TAG),
                            protected)
        res = cls(scaps)
        if tag != cls.TYPE_TAG:
            res.TYPE_TAG = tag
        return res


# TODO: Only use rinterface-level ?
conversion._R_RPY2_MAP.update({
    openrlib.rlib.NILSXP: NULLType,
    openrlib.rlib.EXPRSXP: ExprSexpVector,
    openrlib.rlib.LANGSXP: LangSexpVector,
    openrlib.rlib.ENVSXP: SexpEnvironment,
    openrlib.rlib.RAWSXP: ByteSexpVector,
    openrlib.rlib.LGLSXP: BoolSexpVector,
    openrlib.rlib.INTSXP: IntSexpVector,
    openrlib.rlib.REALSXP: FloatSexpVector,
    openrlib.rlib.CPLXSXP: ComplexSexpVector,
    openrlib.rlib.STRSXP: StrSexpVector,
    openrlib.rlib.VECSXP: ListSexpVector,
    openrlib.rlib.LISTSXP: PairlistSexpVector,
    openrlib.rlib.CLOSXP: SexpClosure,
    openrlib.rlib.BUILTINSXP: SexpClosure,
    openrlib.rlib.SPECIALSXP: SexpClosure,
    openrlib.rlib.EXTPTRSXP: SexpExtPtr,
    openrlib.rlib.SYMSXP: SexpSymbol,
    openrlib.rlib.S4SXP: SexpS4
    })
conversion._R_RPY2_DEFAULT_MAP = Sexp

conversion._PY_RPY2_MAP.update({
    int: conversion._int_to_sexp,
    float: conversion._float_to_sexp
    })

conversion._PY_R_MAP.update({
    _rinterface.ffi.CData: False,
    # integer
    int: conversion._int_to_sexp,
    na_values.NAIntegerType: conversion._int_to_sexp,
    # float
    float: conversion._float_to_sexp,
    na_values.NARealType: conversion._float_to_sexp,
    # boolean
    bool: conversion._bool_to_sexp,
    na_values.NALogicalType: conversion._bool_to_sexp,
    # string
    str: conversion._str_to_sexp,
    sexp.CharSexp: None,
    na_values.NACharacterType: None,
    # complex
    complex: None,
    # None
    type(None): lambda x: openrlib.rlib.R_NilValue})


def vector(iterable, rtype: RTYPES):
    """Create an R vector.

    While the different types of R vectors all have their own class,
    the creation of array in Python is often available through factory
    function that accept the type of the array as a parameters. This
    function is providing a similar functionality for R vectors."""
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
NA = None
NA_Real = None
NA_Complex = None


def initr() -> None:
    """Initialize R's embedded C library."""
    status = embedded._initr()
    atexit.register(endr, 0)
    _rinterface._register_external_symbols()
    _post_initr_setup()
    return status


def _post_initr_setup():

    embedded.emptyenv = SexpEnvironment(
        _rinterface.SexpCapsule(openrlib.rlib.R_EmptyEnv)
    )
    global emptyenv
    emptyenv = embedded.emptyenv

    embedded.baseenv = SexpEnvironment(
        _rinterface.SexpCapsule(openrlib.rlib.R_BaseEnv)
    )
    global baseenv
    baseenv = embedded.baseenv

    embedded.globalenv = SexpEnvironment(
        _rinterface.SexpCapsule(openrlib.rlib.R_GlobalEnv)
    )
    global globalenv
    globalenv = embedded.globalenv

    global NULL
    NULL = NULLType()

    global MissingArg
    MissingArg = _MissingArgType()

    global NA_Character
    na_values.NA_Character = na_values.NACharacterType()
    NA_Character = na_values.NA_Character

    global NA_Integer
    na_values.NA_Integer = na_values.NAIntegerType(openrlib.rlib.R_NaInt)
    NA_Integer = na_values.NA_Integer

    global NA_Logical, NA
    na_values.NA_Logical = na_values.NALogicalType(openrlib.rlib.R_NaInt)
    NA_Logical = na_values.NA_Logical
    NA = NA_Logical

    global NA_Real
    na_values.NA_Real = na_values.NARealType(openrlib.rlib.R_NaReal)
    NA_Real = na_values.NA_Real

    global NA_Complex
    na_values.NA_Complex = _rinterface.ffi.new(
        'Rcomplex *',
        [openrlib.rlib.R_NaReal, openrlib.rlib.R_NaReal])
    NA_Complex = na_values.NA_Complex


def rternalize(function: typing.Callable) -> SexpClosure:
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
