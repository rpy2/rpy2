"""Base definitions for R objects."""

import abc
import collections.abc
from collections import OrderedDict
import enum
import itertools
import typing
from rpy2.rinterface_lib import embedded
from rpy2.rinterface_lib import memorymanagement
from rpy2.rinterface_lib import openrlib
import rpy2.rinterface_lib._rinterface_capi as _rinterface
from rpy2.rinterface_lib._rinterface_capi import _evaluated_promise
from rpy2.rinterface_lib._rinterface_capi import SupportsSEXP
from rpy2.rinterface_lib import conversion
from rpy2.rinterface_lib.conversion import _cdata_res_to_rinterface
from rpy2.rinterface_lib import na_values


class Singleton(type):

    _instances: typing.Dict[typing.Type['Singleton'], 'Singleton'] = {}

    def __call__(cls, *args, **kwargs):
        instances = cls._instances
        if cls not in instances:
            instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return instances[cls]


class SingletonABC(Singleton, abc.ABCMeta):
    pass


class RTYPES(enum.IntEnum):
    """Native R types as defined in R's C API."""

    NILSXP = openrlib.rlib.NILSXP
    SYMSXP = openrlib.rlib.SYMSXP
    LISTSXP = openrlib.rlib.LISTSXP
    CLOSXP = openrlib.rlib.CLOSXP
    ENVSXP = openrlib.rlib.ENVSXP
    PROMSXP = openrlib.rlib.PROMSXP
    LANGSXP = openrlib.rlib.LANGSXP
    SPECIALSXP = openrlib.rlib.SPECIALSXP
    BUILTINSXP = openrlib.rlib.BUILTINSXP
    CHARSXP = openrlib.rlib.CHARSXP
    LGLSXP = openrlib.rlib.LGLSXP
    INTSXP = openrlib.rlib.INTSXP
    REALSXP = openrlib.rlib.REALSXP
    CPLXSXP = openrlib.rlib.CPLXSXP
    STRSXP = openrlib.rlib.STRSXP
    DOTSXP = openrlib.rlib.DOTSXP
    ANYSXP = openrlib.rlib.ANYSXP
    VECSXP = openrlib.rlib.VECSXP
    EXPRSXP = openrlib.rlib.EXPRSXP
    BCODESXP = openrlib.rlib.BCODESXP
    EXTPTRSXP = openrlib.rlib.EXTPTRSXP
    WEAKREFSXP = openrlib.rlib.WEAKREFSXP
    RAWSXP = openrlib.rlib.RAWSXP
    S4SXP = openrlib.rlib.S4SXP

    NEWSXP = openrlib.rlib.NEWSXP
    FREESXP = openrlib.rlib.FREESXP

    FUNSXP = openrlib.rlib.FUNSXP


# The following constants can be use to create Python proxies
# for R objects while R has not been initialized yet.
UNINIT_CAPSULE_CHAR = _rinterface.UninitializedRCapsule(RTYPES.CHARSXP.value)
UNINIT_CAPSULE_INTEGER = _rinterface.UninitializedRCapsule(RTYPES.INTSXP.value)
UNINIT_CAPSULE_LOGICAL = _rinterface.UninitializedRCapsule(RTYPES.LGLSXP.value)
UNINIT_CAPSULE_REAL = _rinterface.UninitializedRCapsule(RTYPES.REALSXP.value)
UNINIT_CAPSULE_CPLX = _rinterface.UninitializedRCapsule(RTYPES.CPLXSXP.value)
UNINIT_CAPSULE_ENV = _rinterface.UninitializedRCapsule(RTYPES.ENVSXP.value)


class Sexp(SupportsSEXP):
    """Base class for R objects.

    The name of a class corresponds to the name SEXP
    used in R's C API."""

    __slots__ = ('_sexpobject', )

    def __init__(self,
                 sexp: typing.Union[SupportsSEXP,
                                    '_rinterface.SexpCapsule',
                                    '_rinterface.UninitializedRCapsule']):
        if isinstance(sexp, SupportsSEXP):
            self._sexpobject = sexp.__sexp__
        elif isinstance(sexp, _rinterface.CapsuleBase):
            self._sexpobject = sexp
        else:
            raise ValueError(
                'The constructor must be called '
                'with an instance of rpy2.rinterface.Sexp '
                'or an instance of '
                'rpy2.rinterface._rinterface.SexpCapsule')

    def __repr__(self) -> str:
        return super().__repr__() + (' [%s]' % self.typeof)

    @property
    def __sexp__(self) -> '_rinterface.CapsuleBase':
        """Access to the underlying C pointer to the R object.

        When assigning a new SexpCapsule to this attribute, the
        R C-level type of the new capsule must be equal to the
        type of the old capsule. A ValueError is raised otherwise."""
        return self._sexpobject

    @__sexp__.setter
    def __sexp__(self,
                 value: '_rinterface.CapsuleBase') -> None:
        assert isinstance(value, _rinterface.SexpCapsule)
        if value.typeof != self.__sexp__.typeof:
            raise ValueError('New capsule type mismatch: %s' %
                             RTYPES(value.typeof))
        self._sexpobject = value

    @property
    def __sexp_refcount__(self) -> int:
        """Count the number of independent Python references to
        the underlying R object."""
        return _rinterface._R_PRESERVED[
            _rinterface.get_rid(self.__sexp__._cdata)
        ]

    def __getstate__(self) -> bytes:
        with memorymanagement.rmemory() as rmemory:
            ser = rmemory.protect(
                _rinterface.serialize(
                    self.__sexp__._cdata,
                    globalenv.__sexp__._cdata)
            )
            n = openrlib.rlib.Rf_xlength(ser)
            res = bytes(_rinterface.ffi.buffer(openrlib.rlib.RAW(ser), n))
        return res

    def __setstate__(self, state: bytes) -> None:
        self._sexpobject = unserialize(state)

    @property
    def rclass(self) -> 'StrSexpVector':
        """Get or set the R "class" attribute for the object."""
        return rclass_get(self.__sexp__)

    @rclass.setter
    def rclass(self,
               value: 'typing.Union[StrSexpVector, str]'):
        rclass_set(self.__sexp__, value)

    @property
    def rid(self) -> int:
        """ID of the underlying R object (memory address)."""
        return _rinterface.get_rid(self.__sexp__._cdata)

    @property
    def typeof(self) -> RTYPES:
        return RTYPES(_rinterface._TYPEOF(self.__sexp__._cdata))

    @property
    def named(self) -> int:
        return _rinterface._NAMED(self.__sexp__._cdata)

    @conversion._cdata_res_to_rinterface
    def list_attrs(self) -> 'typing.Union[StrSexpVector, str]':
        return _rinterface._list_attrs(self.__sexp__._cdata)

    @conversion._cdata_res_to_rinterface
    def do_slot(self, name: str) -> None:
        _rinterface._assert_valid_slotname(name)
        cchar = conversion._str_to_cchar(name)
        with memorymanagement.rmemory() as rmemory:
            name_r = rmemory.protect(openrlib.rlib.Rf_install(cchar))
            if not _rinterface._has_slot(self.__sexp__._cdata, name_r):
                raise LookupError(name)
            res = openrlib.rlib.R_do_slot(self.__sexp__._cdata, name_r)
        return res

    def do_slot_assign(self, name: str, value) -> None:
        _rinterface._assert_valid_slotname(name)
        cchar = conversion._str_to_cchar(name)
        with memorymanagement.rmemory() as rmemory:
            name_r = rmemory.protect(openrlib.rlib.Rf_install(cchar))
            cdata = rmemory.protect(conversion._get_cdata(value))
            openrlib.rlib.R_do_slot_assign(self.__sexp__._cdata,
                                           name_r,
                                           cdata)

    @conversion._cdata_res_to_rinterface
    def get_attrib(self, name: str) -> 'Sexp':
        res = openrlib.rlib.Rf_getAttrib(self.__sexp__._cdata,
                                         conversion._str_to_charsxp(name))
        return res

    # TODO: deprecate this (and implement __eq__) ?
    def rsame(self, sexp) -> bool:
        if isinstance(sexp, Sexp):
            return self.__sexp__._cdata == sexp.__sexp__._cdata
        elif isinstance(sexp, _rinterface.SexpCapsule):
            return sexp._cdata == sexp._cdata
        else:
            raise ValueError('Not an R object.')

    @property
    def names(self) -> 'Sexp':
        return baseenv['names'](self)

    @names.setter
    def names(self, value) -> None:
        if not isinstance(value, StrSexpVector):
            raise ValueError('The new names should be a StrSexpVector.')
        openrlib.rlib.Rf_namesgets(
            self.__sexp__._cdata, value.__sexp__._cdata)

    @property  # type: ignore
    @conversion._cdata_res_to_rinterface
    def names_from_c_attribute(self) -> 'Sexp':
        return openrlib.rlib.Rf_getAttrib(
            self.__sexp__._cdata,
            openrlib.rlib.R_NameSymbol)


class NULLType(Sexp, metaclass=SingletonABC):
    """A singleton class for R's NULL."""

    def __init__(self):
        if embedded.isready():
            tmp = Sexp(
                _rinterface.UnmanagedSexpCapsule(
                    openrlib.rlib.R_NilValue
                )
            )
        else:
            tmp = Sexp(_rinterface.UninitializedRCapsule(RTYPES.NILSXP.value))
        super().__init__(tmp)

    def __bool__(self) -> bool:
        """This is always False."""
        return False

    @property
    def __sexp__(self) -> _rinterface.CapsuleBase:
        return self._sexpobject

    @__sexp__.setter
    def __sexp__(self, value) -> None:
        raise TypeError('The capsule for the R object cannot be modified.')

    @property
    def rid(self) -> int:
        return self._sexpobject.rid


class CETYPE(enum.Enum):
    """Character encodings for R string."""
    CE_NATIVE = openrlib.rlib.CE_NATIVE
    CE_UTF8 = openrlib.rlib.CE_UTF8
    CE_LATIN1 = openrlib.rlib.CE_LATIN1
    CE_BYTES = openrlib.rlib.CE_BYTES
    CE_SYMBOL = openrlib.rlib.CE_SYMBOL
    CE_ANY = openrlib.rlib.CE_ANY


class NCHAR_TYPE(enum.Enum):
    """Type of string scalar in R."""
    Bytes = 0
    Chars = 1
    Width = 2


class CharSexp(Sexp):
    """R's internal (C API-level) scalar for strings."""

    _R_TYPE = openrlib.rlib.CHARSXP
    _NCHAR_MSG = openrlib.ffi.new('char []', b'rpy2.rinterface.CharSexp.nchar')

    @property
    def encoding(self) -> CETYPE:
        return CETYPE(
            openrlib.rlib.Rf_getCharCE(self.__sexp__._cdata)
        )

    def nchar(self, what: NCHAR_TYPE = NCHAR_TYPE.Bytes) -> int:
        # TODO: nchar_type is not parsed properly by cffi ?
        return openrlib.rlib.R_nchar(self.__sexp__._cdata,
                                     what.value,
                                     openrlib.rlib.FALSE,
                                     openrlib.rlib.FALSE,
                                     self._NCHAR_MSG)


class SexpEnvironment(Sexp):
    """Proxy for an R "environment" object.

    An R "environment" object can be thought of as a mix of a
    mapping (like a `dict`) and a scope. To make it more "Pythonic",
    both aspects are kept separate and the method `__getitem__` will
    get an item as it would for a Python `dict` while the method `find`
    will get an item as if it was a scope.

    As soon as R is initialized the following main environments become
    available to the user:
    - `globalenv`: The "workspace" for the current R process. This can
      be thought of as when `__name__ == '__main__'` in Python.
    - `baseenv`: The namespace of R's "base" package.
    """

    @_cdata_res_to_rinterface
    @_evaluated_promise
    def find(self,
             key: str,
             wantfun: bool = False) -> Sexp:
        """Find an item, starting with this R environment.

        Raises a `KeyError` if the key cannot be found.

        This method is called `find` because it is somewhat different
        from the method :meth:`get` in Python mappings such :class:`dict`.
        This is looking for a key across enclosing environments, returning
        the first key found."""

        if not isinstance(key, str):
            raise TypeError('The key must be a non-empty string.')
        elif not len(key):
            raise ValueError('The key must be a non-empty string.')
        with memorymanagement.rmemory() as rmemory:
            key_cchar = conversion._str_to_cchar(key, 'utf-8')
            symbol = rmemory.protect(
                openrlib.rlib.Rf_install(key_cchar)
            )
            if wantfun:
                # One would expect this to be like
                #   res = _rinterface._findfun(symbol, self.__sexp__._cdata)
                # but R's findfun will segfault if the symbol is not in
                # the environment. :/
                rho = self
                while rho.rid != emptyenv.rid:
                    res = rmemory.protect(
                        _rinterface.findvar_in_frame_wrap(
                            rho.__sexp__._cdata, symbol
                        )
                    )
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
        if not isinstance(key, str):
            raise TypeError('The key must be a non-empty string.')
        elif not len(key):
            raise ValueError('The key must be a non-empty string.')
        embedded.assert_isready()
        with memorymanagement.rmemory() as rmemory:
            key_cchar = conversion._str_to_cchar(key)
            symbol = rmemory.protect(
                openrlib.rlib.Rf_install(key_cchar)
            )
            res = rmemory.protect(
                _rinterface.findvar_in_frame_wrap(
                    self.__sexp__._cdata, symbol
                )
            )

        # TODO: move check of R_UnboundValue to _rinterface
        if res == openrlib.rlib.R_UnboundValue:
            raise KeyError("'%s' not found" % key)
        return res

    def __setitem__(self, key: str, value) -> None:
        # TODO: move body to _rinterface-level function
        if not isinstance(key, str):
            raise TypeError('The key must be a non-empty string.')
        elif not len(key):
            raise ValueError('The key must be a non-empty string.')
        if (self.__sexp__._cdata == openrlib.rlib.R_BaseEnv) or \
           (self.__sexp__._cdata == openrlib.rlib.R_EmptyEnv):
            raise ValueError('Cannot remove variables from the base or '
                             'empty environments.')
        # TODO: call to Rf_duplicate needed ?
        with memorymanagement.rmemory() as rmemory:
            key_cchar = conversion._str_to_cchar(key)
            symbol = rmemory.protect(
                openrlib.rlib.Rf_install(key_cchar)
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

    def __delitem__(self, key: str) -> None:
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
    def frame(self) -> 'typing.Union[NULLType, SexpEnvironment]':
        """Get the parent frame of the environment."""
        return openrlib.rlib.FRAME(self.__sexp__._cdata)

    @property  # type: ignore
    @_cdata_res_to_rinterface
    def enclos(self) -> 'typing.Union[NULLType, SexpEnvironment]':
        """Get or set the enclosing environment."""
        return openrlib.rlib.ENCLOS(self.__sexp__._cdata)

    @enclos.setter
    def enclos(self, value: 'SexpEnvironment') -> None:
        assert isinstance(value, SexpEnvironment)
        openrlib.rlib.SET_ENCLOS(self.__sexp__._cdata,
                                 value.__sexp__._cdata)

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
                _ = _rinterface._string_getitem(symbols, i)
                if _ is None:
                    raise TypeError(
                        'R symbol string should not be able to be NA.'
                    )
                res.append(_)
        for e in res:
            yield e

    def __iter__(self) -> typing.Generator[str, None, None]:
        """See method `keys()`."""
        return self.keys()

    def is_locked(self) -> bool:
        return openrlib.rlib.R_EnvironmentIsLocked(
            self.__sexp__._cdata)


emptyenv = SexpEnvironment(UNINIT_CAPSULE_ENV)
baseenv = SexpEnvironment(UNINIT_CAPSULE_ENV)
globalenv = SexpEnvironment(UNINIT_CAPSULE_ENV)
NULL = NULLType()

VT = typing.TypeVar('VT', bound='SexpVector')


# TODO: move to _rinterface-level function (as ABI / API compatibility
# will have API-defined code compile for efficiency).
def _populate_r_vector(iterable, r_vector, set_elt, cast_value) -> None:
    for i, v in enumerate(iterable):
        set_elt(r_vector, i, cast_value(v))


class SexpVectorAbstract(SupportsSEXP, metaclass=abc.ABCMeta):

    @property
    @abc.abstractmethod
    def _R_TYPE(self):
        pass

    @property
    @abc.abstractmethod
    def _R_SIZEOF_ELT(self):
        pass

    @staticmethod
    @abc.abstractmethod
    def _CAST_IN(o):
        pass

    @staticmethod
    @abc.abstractmethod
    def _R_SET_VECTOR_ELT(x, i, v):
        pass

    @staticmethod
    @abc.abstractmethod
    def _R_VECTOR_ELT(x, i):
        pass

    @staticmethod
    @abc.abstractmethod
    def _R_GET_PTR(o):
        pass

    @classmethod
    @_cdata_res_to_rinterface
    def from_iterable(cls, iterable,
                      populate_func=None,
                      set_elt=None,
                      cast_value=None) -> VT:
        """Create an R vector/array from an iterable."""
        if not embedded.isready():
            raise embedded.RNotReadyError('Embedded R is not ready to use.')
        if populate_func is None:
            populate_func = _populate_r_vector
        if set_elt is None:
            set_elt = cls._R_SET_VECTOR_ELT
        if cast_value is None:
            cast_value = cls._CAST_IN
        n = len(iterable)
        with memorymanagement.rmemory() as rmemory:
            r_vector = rmemory.protect(
                openrlib.rlib.Rf_allocVector(
                    cls._R_TYPE, n)
            )
            populate_func(iterable, r_vector, set_elt, cast_value)
        return r_vector

    @classmethod
    def _raise_incompatible_C_size(cls, mview):
        msg = (
            'Incompatible C type sizes. '
            'The R array type is "{r_type}" with {r_size} byte{r_size_pl} '
            'per item '
            'while the Python array type is "{py_type}" with {py_size} '
            'byte{py_size_pl} per item.'
            .format(r_type=cls._R_TYPE,
                    r_size=cls._R_SIZEOF_ELT,
                    r_size_pl='s' if cls._R_SIZEOF_ELT > 1 else '',
                    py_type=mview.format,
                    py_size=mview.itemsize,
                    py_size_pl='s' if mview.itemsize > 1 else '')
        )
        raise ValueError(msg)

    @classmethod
    def _check_C_compatible(cls, mview):
        return mview.itemsize == cls._R_SIZEOF_ELT

    @classmethod
    @_cdata_res_to_rinterface
    def from_memoryview(cls, mview: memoryview) -> VT:
        """Create an R vector/array from a memoryview.

        The memoryview must be contiguous, and the C representation
        for the vector must be compatible between R and Python. If
        not the case, a :class:`ValueError` exception with will be
        raised."""
        if not embedded.isready():
            raise embedded.RNotReadyError('Embedded R is not ready to use.')
        if not mview.contiguous:
            raise ValueError('The memory view must be contiguous.')
        if not cls._check_C_compatible(mview):
            cls._raise_incompatible_C_size(mview)

        r_vector = None
        n = len(mview)
        with memorymanagement.rmemory() as rmemory:
            r_vector = rmemory.protect(
                openrlib.rlib.Rf_allocVector(
                    cls._R_TYPE, n)
            )
            dest_ptr = cls._R_GET_PTR(r_vector)
            src_ptr = _rinterface.ffi.from_buffer(mview)
            nbytes = n * mview.itemsize
            _rinterface.ffi.memmove(dest_ptr, src_ptr, nbytes)
        return r_vector

    @classmethod
    def from_object(cls, obj) -> VT:
        """Create an R vector/array from a Python object, if possible.

        An exception :class:`ValueError` will be raised if not possible."""
        try:
            mv = memoryview(obj)
            res = cls.from_memoryview(mv)
        except (TypeError, ValueError):
            try:
                res = cls.from_iterable(obj)
            except ValueError:
                msg = ('The class methods from_memoryview() and '
                       'from_iterable() both failed to make a {} '
                       'from an object of class {}'
                       .format(cls, type(obj)))
                raise ValueError(msg)
        return res

    def __getitem__(
            self,
            i: typing.Union[int, slice]) -> typing.Union[Sexp, VT, typing.Any]:
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            res = conversion._cdata_to_rinterface(
                self._R_VECTOR_ELT(cdata, i_c))
        elif isinstance(i, slice):
            res = self.from_iterable(
                [
                    self._R_VECTOR_ELT(
                        cdata, i_c,
                    ) for i_c in range(*i.indices(len(self)))
                ],
                cast_value=lambda x: x
            )
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))
        return res

    def __setitem__(self, i: typing.Union[int, slice], value) -> None:
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            if isinstance(value, Sexp):
                val_cdata = value.__sexp__._cdata
            else:
                val_cdata = conversion._python_to_cdata(value)
            self._R_SET_VECTOR_ELT(cdata, i_c,
                                   val_cdata)
        elif isinstance(i, slice):
            for i_c, v in zip(range(*i.indices(len(self))), value):
                self._R_SET_VECTOR_ELT(cdata, i_c,
                                       v.__sexp__._cdata)
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))

    def __len__(self) -> int:
        return openrlib.rlib.Rf_xlength(self.__sexp__._cdata)

    def __iter__(self) -> typing.Iterator[typing.Union[Sexp, VT, typing.Any]]:
        for i in range(len(self)):
            yield self[i]

    def index(self, item: typing.Any) -> int:
        for i, e in enumerate(self):
            if e == item:
                return i
        raise ValueError("'%s' is not in R vector" % item)


class SexpVector(Sexp, SexpVectorAbstract):
    """Base abstract class for R vector objects.

    R vector objects are, at the C level, essentially C arrays wrapped in
    the general structure for R objects."""

    def __init__(self,
                 obj: typing.Union[_rinterface.SexpCapsule,
                                   collections.abc.Sized]):
        if (
                isinstance(obj, Sexp)
                or
                isinstance(obj, _rinterface.SexpCapsule)
        ):
            super().__init__(obj)
        elif isinstance(obj, collections.abc.Sized):
            robj: Sexp = type(self).from_object(obj)
            super().__init__(robj)
        else:
            raise TypeError('The constructor must be called '
                            'with an instance of '
                            'rpy2.rinterface.Sexp '
                            'or an instance of '
                            'rpy2.rinterface._rinterface.SexpCapsule')


def _as_charsxp_cdata(x: typing.Union[CharSexp, str]):
    if isinstance(x, CharSexp):
        return x.__sexp__._cdata
    else:
        return conversion._str_to_charsxp(x)


class StrSexpVector(SexpVector):
    """R vector of strings."""

    _R_TYPE = openrlib.rlib.STRSXP
    _R_GET_PTR = openrlib._STRING_PTR
    _R_SIZEOF_ELT = None
    _R_VECTOR_ELT = openrlib.rlib.STRING_ELT
    _R_SET_VECTOR_ELT = openrlib.rlib.SET_STRING_ELT
    _CAST_IN = _as_charsxp_cdata

    def __getitem__(
            self,
            i: typing.Union[int, slice]
    ) -> typing.Union['StrSexpVector', str, 'NACharacterType']:
        cdata = self.__sexp__._cdata
        res: typing.Union['StrSexpVector', str, 'NACharacterType']
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            _ = _rinterface._string_getitem(cdata, i_c)
            if _ is None:
                res = na_values.NA_Character  # type: ignore
            else:
                res = _
        elif isinstance(i, slice):
            res = self.from_iterable(
                [_rinterface._string_getitem(cdata, i_c)
                 for i_c in range(*i.indices(len(self)))]
            )
        else:
            raise TypeError('Indices must be integers or slices,'
                            ' not %s' % type(i))
        return res

    def __setitem__(
            self,
            i: typing.Union[int, slice],
            value: typing.Union[str, typing.Sequence[typing.Optional[str]],
                                'StrSexpVector', 'NACharacterType']
    ) -> None:
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            if isinstance(value, Sexp):
                val_cdata = value.__sexp__._cdata
            else:
                if not isinstance(value, str):
                    value = str(value)
                val_cdata = _as_charsxp_cdata(value)
            self._R_SET_VECTOR_ELT(
                cdata, i_c,
                val_cdata
            )
        elif isinstance(i, slice):
            value_slice: typing.Iterable
            if (
                    isinstance(value, NACharacterType)
                    or
                    isinstance(value, str)
            ):
                value_slice = itertools.cycle((value, ))
            elif len(value) == 1:
                value_slice = itertools.cycle(value)
            else:
                value_slice = value
            for i_c, _ in zip(range(*i.indices(len(self))), value_slice):
                if _ is None:
                    v_cdata = openrlib.rlib.R_NaString
                else:
                    if isinstance(_, str):
                        v = _
                    else:
                        v = str(_)
                    v_cdata = _as_charsxp_cdata(v)
                self._R_SET_VECTOR_ELT(
                    cdata, i_c,
                    v_cdata
                )
        else:
            raise TypeError('Indices must be integers or slices, '
                            'not %s' % type(i))

    def get_charsxp(self, i: int) -> CharSexp:
        """Get the R CharSexp objects for the index i."""
        i_c = _rinterface._python_index_to_c(self.__sexp__._cdata, i)
        return CharSexp(
            _rinterface.SexpCapsule(
                openrlib.rlib.STRING_ELT(self.__sexp__._cdata, i_c)
            )
        )


class RVersion(metaclass=Singleton):

    _version = None

    def __init__(self):
        assert embedded.isinitialized()
        robj = StrSexpVector(['R.version'])
        with memorymanagement.rmemory() as rmemory:
            parsed = _rinterface._parse(robj.__sexp__._cdata, 1, rmemory)
        res = baseenv['eval'](parsed)
        self._version = OrderedDict((k, v[0]) for k, v in zip(res.names, res))

    def __getitem__(self, k):
        return self._version[k]

    def keys(self):
        return self._version.keys()


_TYPE2STR = {
    RTYPES.NILSXP: 'NULL',
    RTYPES.SYMSXP: 'symbol',  # alias: name
    RTYPES.LISTSXP: 'pairlist',
    RTYPES.CLOSXP: 'closure',
    RTYPES.ENVSXP: 'environment',
    RTYPES.PROMSXP: 'promise',
    RTYPES.LANGSXP: 'language',
    RTYPES.SPECIALSXP: 'special',
    RTYPES.BUILTINSXP: 'builtin',
    RTYPES.CHARSXP: 'char',
    RTYPES.LGLSXP: 'logical',
    RTYPES.INTSXP: 'integer',
    RTYPES.REALSXP: 'double',  # alias: numeric
    RTYPES.CPLXSXP: 'complex',
    RTYPES.STRSXP: 'character',
    RTYPES.DOTSXP: '...',
    RTYPES.ANYSXP: 'any',
    RTYPES.EXPRSXP: 'expression',
    RTYPES.VECSXP: 'list',
    RTYPES.EXTPTRSXP: 'externalptr',
    RTYPES.BCODESXP: 'bytecode',
    RTYPES.WEAKREFSXP: 'weakref',
    RTYPES.RAWSXP: 'raw',
    RTYPES.S4SXP: 'S4'
}


def rclass_get(scaps: _rinterface.CapsuleBase) -> StrSexpVector:
    """ Get the R class name.

    If no specific attribute "class" is defined from the objects, this
    will perform the equivalent of R_data_class()
    (src/main/attrib.c in the R source code).
    """
    rlib = openrlib.rlib
    with memorymanagement.rmemory() as rmemory:
        classes = rmemory.protect(
            rlib.Rf_getAttrib(scaps._cdata,
                              rlib.R_ClassSymbol))
        if rlib.Rf_length(classes) == 0:
            classname: typing.Tuple[str, ...]
            dim = rmemory.protect(
                rlib.Rf_getAttrib(scaps._cdata,
                                  rlib.R_DimSymbol))
            ndim = rlib.Rf_length(dim)
            if ndim > 0:
                if ndim == 2:
                    if int(RVersion()['major']) >= 4:
                        classname = ('matrix', 'array')
                    else:
                        classname = ('matrix', )
                else:
                    classname = ('array', )
            else:
                typeof = RTYPES(scaps.typeof)
                if typeof in (RTYPES.CLOSXP,
                              RTYPES.SPECIALSXP,
                              RTYPES.BUILTINSXP):
                    classname = ('function', )
                elif typeof == RTYPES.REALSXP:
                    classname = ('numeric', )
                elif typeof == RTYPES.SYMSXP:
                    classname = ('name', )
                elif typeof == RTYPES.LANGSXP:
                    symb = rlib.CAR(scaps._cdata)
                    if openrlib.rlib.Rf_isSymbol(symb):
                        symb_rstr = openrlib.rlib.PRINTNAME(symb)
                        symb_str = conversion._cchar_to_str(
                            openrlib.rlib.R_CHAR(symb_rstr),
                            conversion._R_ENC_PY[openrlib.rlib
                                                 .Rf_getCharCE(symb_rstr)]
                        )
                        if symb_str in ('if', 'while', 'for', '=',
                                        '<-', '(', '{'):
                            classname = (symb_str, )
                        else:
                            classname = ('call', )
                    else:
                        classname = ('call', )
                else:
                    classname = (_TYPE2STR.get(typeof, str(typeof)), )
            classes = StrSexpVector.from_iterable(classname)
        else:
            classes = conversion._cdata_to_rinterface(classes)
    return classes


def rclass_set(
        scaps: _rinterface.CapsuleBase,
        value: 'typing.Union[StrSexpVector, str]'
) -> None:
    """ Set the R class.

    :param:`scaps` A capsule with a pointer to an R object.
    :param:`value` An R vector of strings."""
    if isinstance(value, StrSexpVector):
        value_r = value
    elif isinstance(value, str):
        value_r = StrSexpVector.from_iterable(
            [value])
    else:
        raise TypeError('Value should a str or '
                        'a rpy2.rinterface.sexp.StrSexpVector.')
    openrlib.rlib.Rf_setAttrib(scaps._cdata,
                               openrlib.rlib.R_ClassSymbol,
                               value_r.__sexp__._cdata)


def unserialize(state):
    n = len(state)
    with memorymanagement.rmemory() as rmemory:
        cdata = rmemory.protect(
            openrlib.rlib.Rf_allocVector(openrlib.rlib.RAWSXP, n))
        _rinterface.ffi.memmove(
            openrlib.rlib.RAW(cdata), state, n)
        ser = rmemory.protect(
            _rinterface.unserialize(cdata,
                                    globalenv.__sexp__._cdata)
        )
        res = _rinterface.SexpCapsule(ser)
    return res


class NAIntegerType(int, metaclass=Singleton):

    def __new__(cls, *args, **kwargs):
        embedded.assert_isready()
        return super().__new__(cls, openrlib.rlib.R_NaInt)

    def __repr__(self) -> str:
        return 'NA_integer_'

    def __str__(self) -> str:
        return 'NA_integer_'

    def __bool__(self):
        raise ValueError('R value for missing integer value')


class NACharacterType(CharSexp, metaclass=SingletonABC):

    def __init__(self):
        embedded.assert_isready()
        super().__init__(
            CharSexp(
                _rinterface.SexpCapsule(openrlib.rlib.R_NaString)
            )
        )

    def __repr__(self) -> str:
        return 'NA_character_'

    def __str__(self) -> str:
        return 'NA_character_'

    def __bool__(self):
        raise ValueError('R value for missing character value')


class NALogicalType(int, metaclass=Singleton):

    def __new__(cls, *args, **kwargs):
        embedded.assert_isready()
        return super().__new__(cls, openrlib.rlib.R_NaInt)

    def __repr__(self) -> str:
        return 'NA'

    def __str__(self) -> str:
        return 'NA'

    def __bool__(self) -> bool:
        raise ValueError('R value for missing boolean value')


class NARealType(float, metaclass=Singleton):

    def __new__(cls, *args, **kwargs):
        embedded.assert_isready()
        return super().__new__(cls, openrlib.rlib.R_NaReal)

    def __repr__(self) -> str:
        return 'NA_real_'

    def __str__(self) -> str:
        return 'NA_real_'

    def __bool__(self) -> bool:
        raise ValueError('R value for missing float value')


class NAComplexType(complex, metaclass=Singleton):

    def __new__(cls, *args, **kwargs):
        embedded.assert_isready()
        return super().__new__(cls,
                               openrlib.rlib.R_NaReal,
                               openrlib.rlib.R_NaReal)

    def __repr__(self) -> str:
        return 'NA_complex_'

    def __str__(self) -> str:
        return 'NA_complex_'

    def __bool__(self):
        raise ValueError('R value for missing complex value')
