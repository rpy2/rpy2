"""Base definitions for R objects."""

import abc
import collections
import enum
import typing
from . import embedded
from . import memorymanagement
from . import openrlib
from . import _rinterface_capi as _rinterface
from . import conversion


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


class Sexp(object):
    """Base class for R objects.

    The name of a class corresponds to the name SEXP
    used in R's C API."""

    __slots__ = ('_sexpobject', )

    def __init__(self, sexp: typing.Union['Sexp', '_rinterface.SexpCapsule']):
        if not embedded.isready():
            raise embedded.RNotReadyError('Embedded R is not ready to use.')

        if isinstance(sexp, Sexp):
            self._sexpobject = sexp.__sexp__
        elif isinstance(sexp, _rinterface.SexpCapsule):
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
    def __sexp__(self) -> '_rinterface.SexpCapsule':
        """Access to the underlying C pointer to the R object.

        When assigning a new SexpCapsule to this attribute, the
        R C-level type of the new capsule must be equal to the
        type of the old capsule. A ValueError is raised otherwise."""
        return self._sexpobject

    @__sexp__.setter
    def __sexp__(self,
                 value: '_rinterface.SexpCapsule') -> None:
        assert isinstance(value, _rinterface.SexpCapsule)
        if value.typeof != self.__sexp__.typeof:
            raise ValueError('New capsule type mismatch: %s' %
                             RTYPES(value.typeof))
        self._sexpobject = value

    @property
    def __sexp_refcount__(self):
        """Count the number of independent Python references to
        the underlyinh R object."""
        return _rinterface._R_PRESERVED[
            _rinterface.get_rid(self.__sexp__._cdata)
        ]

    def __getstate__(self) -> bytes:
        with memorymanagement.rmemory() as rmemory:
            ser = rmemory.protect(
                _rinterface.serialize(self.__sexp__._cdata,
                                      embedded.globalenv.__sexp__._cdata)
            )
            n = openrlib.rlib.Rf_xlength(ser)
            res = bytes(_rinterface.ffi.buffer(openrlib.rlib.RAW(ser), n))
        return res

    def __setstate__(self, state: bytes) -> None:
        self._sexpobject = unserialize(state)

    @property
    def rclass(self):
        return rclass_get(self.__sexp__)

    @rclass.setter
    def rclass(self, value):
        if isinstance(value, StrSexpVector):
            value_r = value
        elif isinstance(value, str):
            value_r = StrSexpVector.from_iterable(
                [value])
        openrlib.rlib.Rf_setAttrib(self.__sexp__._cdata,
                                   openrlib.rlib.R_ClassSymbol,
                                   value_r.__sexp__._cdata)

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
    def list_attrs(self):
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
    def get_attrib(self, name: str):
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
    def names(self):
        # TODO: force finding function
        return embedded.globalenv.get('names')(self)

    @names.setter
    def names(self, value) -> None:
        if not isinstance(value, StrSexpVector):
            raise ValueError('The new names should be a StrSexpVector.')
        openrlib.rlib.Rf_namesgets(
            self.__sexp__._cdata, value.__sexp__._cdata)

    @property
    @conversion._cdata_res_to_rinterface
    def names_from_c_attribute(self):
        return openrlib.rlib.Rf_getAttrib(
            self.__sexp__._cdata,
            openrlib.rlib.R_NameSymbol)


class CETYPE(enum.Enum):
    """Character encodings."""
    CE_NATIVE = 0
    CE_UTF8 = 1
    CE_LATIN1 = 2
    CE_BYTES = 3
    CE_SYMBOL = 5
    CE_ANY = 99


class NCHAR_TYPE(enum.Enum):
  Bytes = 0
  Chars = 1 
  Width = 2


class CharSexp(Sexp):
    """R's internal (C API-level) scalar string."""
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


# TODO: move to _rinterface-level function (as ABI / API compatibility
# will have API-defined code compile for efficiency).
def _populate_r_vector(iterable, r_vector, set_elt, cast_value):
    for i, v in enumerate(iterable):
        set_elt(r_vector, i, cast_value(v))


VT = typing.TypeVar('VT', bound='SexpVector')


class SexpVector(Sexp, metaclass=abc.ABCMeta):
    """Base class for R vector objects.

    R vector objects are, at the C level, essentially C arrays wrapped in
    the general structure for R objects."""

    @property
    @abc.abstractmethod
    def _R_TYPE(self):
        pass

    @staticmethod
    @abc.abstractmethod
    def _CAST_IN(self):
        pass

    @staticmethod
    @abc.abstractmethod
    def _R_SET_VECTOR_ELT(self):
        pass

    @staticmethod
    @abc.abstractmethod
    def _R_VECTOR_ELT(self):
        pass

    @staticmethod
    @abc.abstractmethod
    def _R_GET_PTR(self):
        pass

    def __init__(self,
                 obj: typing.Union[_rinterface.SexpCapsule,
                                   collections.Sized]):
        if isinstance(obj, Sexp) or isinstance(obj,
                                               _rinterface.SexpCapsule):
            super().__init__(obj)
        elif isinstance(obj, collections.Sized):
            super().__init__(type(self).from_iterable(obj).__sexp__)
        else:
            raise ValueError('The constructor must be called '
                             'with that is an instance of '
                             'rpy2.rinterface.Sexp '
                             'or an instance of '
                             'rpy2.rinterface._rinterface.SexpCapsule')

    @classmethod
    @conversion._cdata_res_to_rinterface
    def from_iterable(cls, iterable,
                      cast_in: bool = None) -> VT:
        if not embedded.isready():
            raise embedded.RNotReadyError('Embedded R is not ready to use.')
        if cast_in is None:
            cast_in = cls._CAST_IN
        n = len(iterable)
        with memorymanagement.rmemory() as rmemory:
            r_vector = rmemory.protect(
                openrlib.rlib.Rf_allocVector(
                    cls._R_TYPE, n)
            )
            _populate_r_vector(iterable,
                               r_vector,
                               cls._R_SET_VECTOR_ELT,
                               cast_in)
        return r_vector

    def __getitem__(
            self,
            i: typing.Union[int, slice]) -> typing.Union[Sexp, VT]:
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            res = conversion._cdata_to_rinterface(
                self._R_VECTOR_ELT(cdata, i_c))
        elif isinstance(i, slice):
            res = type(self).from_iterable(
                [
                    self._R_VECTOR_ELT(
                        cdata, i_c
                    ) for i_c in range(*i.indices(len(self)))
                ],
                cast_in=lambda x: x
            )
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))
        return res

    def __setitem__(self, i: typing.Union[int, slice], value) -> None:
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            self._R_SET_VECTOR_ELT(cdata, i_c,
                                   value.__sexp__._cdata)
        elif isinstance(i, slice):
            for i_c, v in zip(range(*i.indices(len(self))), value):
                self._R_SET_VECTOR_ELT(cdata, i_c,
                                       v.__sexp__._cdata)
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))

    def __len__(self):
        return openrlib.rlib.Rf_xlength(self.__sexp__._cdata)

    def index(self, item):
        for i, e in enumerate(self):
            if e == item:
                return i
        raise ValueError("'%s' is not in R vector" % item)


def _as_charsxp_cdata(x: typing.Union[CharSexp, str]):
    if isinstance(x, CharSexp):
        return x.__sexp__._cdata
    else:
        return conversion._str_to_charsxp(x)


class StrSexpVector(SexpVector):
    """R vector of strings."""

    _R_TYPE = openrlib.rlib.STRSXP
    _R_GET_PTR = openrlib._STRING_PTR
    _R_VECTOR_ELT = openrlib.rlib.STRING_ELT
    _R_SET_VECTOR_ELT = openrlib.rlib.SET_STRING_ELT
    _CAST_IN = _as_charsxp_cdata

    def __getitem__(
            self,
            i: typing.Union[int, slice]) -> typing.Union[str, 'StrSexpVector']:
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            res = _rinterface._string_getitem(cdata, i_c)
        elif isinstance(i, slice):
            res = type(self).from_iterable(
                [_rinterface._string_getitem(cdata, i_c)
                 for i_c in range(*i.indices(len(self)))]
            )
        else:
            raise TypeError('Indices must be integers or slices,'
                            ' not %s' % type(i))
        return res

    def __setitem__(self,
                    i: typing.Union[int, slice],
                    value: typing.Union[str, typing.Sequence[str]]) -> None:
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            self._R_SET_VECTOR_ELT(
                cdata, i_c,
                conversion._str_to_charsxp(value)
            )
        elif isinstance(i, slice):
            for i_c, v in zip(range(*i.indices(len(self))), value):
                self._R_SET_VECTOR_ELT(
                    cdata, i_c,
                    conversion._str_to_charsxp(v)
                )
        else:
            raise TypeError('Indices must be integers or slices, '
                            'not %s' % type(i))

    def get_charsxp(self, i: typing.Union[int, slice]) -> CharSexp:
        """Get the R CharSexp objects for the index i."""
        i_c = _rinterface._python_index_to_c(self.__sexp__._cdata, i)
        return CharSexp(
            _rinterface.SexpCapsule(
                openrlib.rlib.STRING_ELT(self.__sexp__._cdata, i_c)
            )
        )


_DEFAULT_RCLASS_NAMES = {
    RTYPES.ENVSXP: 'environment',
    RTYPES.CLOSXP: 'function',
    RTYPES.SPECIALSXP: 'function',
    RTYPES.BUILTINSXP: 'function',
    RTYPES.REALSXP: 'numeric',
    RTYPES.STRSXP: 'character',
    RTYPES.SYMSXP: 'name',
    RTYPES.LANGSXP: 'language'}


def rclass_get(scaps: _rinterface.SexpCapsule) -> StrSexpVector:
    rlib = openrlib.rlib
    with memorymanagement.rmemory() as rmemory:
        classes = rmemory.protect(
            rlib.Rf_getAttrib(scaps._cdata,
                              rlib.R_ClassSymbol))
        if rlib.Rf_length(classes) == 0:
            dim = rmemory.protect(
                rlib.Rf_getAttrib(scaps._cdata,
                                  rlib.R_DimSymbol))
            ndim = rlib.Rf_length(dim)
            if ndim > 0:
                if ndim == 2:
                    classname = 'matrix'
                else:
                    classname = 'array'
            else:
                typeof = RTYPES(scaps.typeof)
                classname = _DEFAULT_RCLASS_NAMES.get(
                    typeof, str(typeof))
            classes = StrSexpVector.from_iterable(
                [classname])
        else:
            classes = conversion._cdata_to_rinterface(classes)
    return classes


def unserialize(state):
    n = len(state)
    with memorymanagement.rmemory() as rmemory:
        cdata = rmemory.protect(
            openrlib.rlib.Rf_allocVector(openrlib.rlib.RAWSXP, n))
        _rinterface.ffi.memmove(
            openrlib.rlib.RAW(cdata), state, n)
        ser = rmemory.protect(
            _rinterface.unserialize(cdata,
                                    embedded.globalenv.__sexp__._cdata)
        )
        res = _rinterface.SexpCapsule(ser)
    return res
