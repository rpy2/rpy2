import collections
import enum
import typing
from . import conversion
from . import embedded
from . import memorymanagement
from . import _rinterface_capi as _rinterface


_cdata_res_to_rinterface = conversion._cdata_res_to_rinterface

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


class Sexp(object):
    
    __slots__ = ('_sexpobject', )

    def __init__(self, sexp):
        if not embedded.isready():
            raise embedded.RNotReadyError('Embedded R is not ready to use.')
        
        if isinstance(sexp, Sexp):
            self._sexpobject = sexp.__sexp__
        elif isinstance(sexp, _rinterface.SexpCapsule):
            self._sexpobject = sexp
        else:
            raise ValueError('The constructor must be called '
                             'with an instance of rpy2.rinterface.Sexp '
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
        with memorymanagement.rmemory() as rmemory:
            ser = rmemory.protect(
                _rinterface.serialize(self.__sexp__._cdata,
                                      embedded.globalenv.__sexp__._cdata)
            )
            n = _rinterface.rlib.Rf_xlength(ser)
            res = bytes(_rinterface.ffi.buffer(_rinterface.rlib.RAW(ser), n))
        return res

    def __setstate__(self, state):
        self._sexpobject = unserialize(state)

    @property
    def rclass(self):
        return rclass_get(self.__sexp__)

    @rclass.setter
    def rclass(self, value):
        if isinstance(value, StrSexpVector):
            value_r = value
        elif isisntance(value, str):
            value_r = StrSexpVector.from_iterable(
                [_rinterface._str_to_charsxp(value)])
        _rinterface.rlib.Rf_setAttrib(self.__sexp__._cdata,
                                      _rinterface.rlib.R_ClassSymbol,
                                      value_r.__sexp__._cdata)
        
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
    def do_slot(self, name: str):
        _rinterface._assert_valid_slotname(name)
        cchar = _rinterface._str_to_cchar(name)
        # TODO: protect ?
        name_r = _rinterface.rlib.Rf_install(cchar)
        if not _rinterface._has_slot(self.__sexp__._cdata, name_r):
            raise LookupError(name)
        return _rinterface.rlib.R_do_slot(self.__sexp__._cdata, name_r)

    def do_slot_assign(self, name: str, value):
        _rinterface._assert_valid_slotname(name)
        cchar = _rinterface._str_to_cchar(name)
        name_r = _rinterface.rlib.Rf_install(cchar)
        _rinterface.rlib.R_do_slot_assign(self.__sexp__._cdata,
                                          name_r,
                                          value.__sexp__._cdata)

    @_cdata_res_to_rinterface
    def get_attrib(self, name: str):
        res = _rinterface.rlib.Rf_getAttrib(self.__sexp__._cdata,
                                            _rinterface._str_to_charsxp(name))
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
    def names(self, value):
        _rinterface.rlib.Rf_namesgets(
            self.__sexp__._cdata, value)

    @property
    @_cdata_res_to_rinterface
    def names_from_c_attribute(self):
        return _rinterface.rlib.Rf_getAttrib(
            self.__sexp__._cdata,
            _rinterface.rlib.R_NameSymbol)


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

    def nchar(self, what=None):  # _rinterface.rlib.nchar_type.Bytes):
        # TODO: nchar_type is not parsed properly by cffi ?
        return _rinterface.rlib.R_nchar(self.__sexp__._cdata,
                                        what,
                                        _rinterface.rlib.FALSE,
                                        _rinterface.rlib.FALSE,
                                        'rpy2.rinterface.CharSexp.nchar')


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
                             'or an instance of '
                             'rpy2.rinterface._rinterface.SexpCapsule')
        
    @classmethod
    @_cdata_res_to_rinterface
    def from_iterable(cls, iterable,
                      cast_in: bool = None):
        if not embedded.isready():
            raise embedded.RNotReadyError('Embedded R is not ready to use.')
        if cast_in is None:
            cast_in = cls._CAST_IN
        n = len(iterable)
        with memorymanagement.rmemory() as rmemory:
            r_vector = rmemory.protect(
                _rinterface.rlib.Rf_allocVector(
                    cls._R_TYPE, n)
            )
            _populate_r_vector(iterable,
                               r_vector,
                               cls._R_SET_ELT,
                               cast_in)
        return r_vector

    def __getitem__(self, i: int) -> typing.Any:
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
    
    def __setitem__(self, i: int, value):
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


def _as_charsxp_cdata(x):
    if isinstance(x, CharSexp):
        return x.__sexp__._cdata
    else:
        return _rinterface._str_to_charsxp(x)


class StrSexpVector(SexpVector):

    _R_TYPE = _rinterface.rlib.STRSXP
    _R_SET_ELT = _rinterface.rlib.SET_STRING_ELT
    _CAST_IN = _as_charsxp_cdata

    def __getitem__(self, i: int):
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

    def __setitem__(self, i: int, value):
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
            raise TypeError('Indices must be integers or slices, '
                            'not %s' % type(i))

    def get_charsxp(self, i: int) -> CharSexp:
        i_c = _rinterface._python_index_to_c(self.__sexp__._cdata, i)
        return CharSexp(
            _rinterface.SexpCapsule(
                _rinterface.rlib.STRING_ELT(self.__sexp__._cdata, i_c)
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


def rclass_get(scaps: _rinterface.SexpCapsule):
    rlib = _rinterface.rlib
    classes = rlib.Rf_getAttrib(scaps._cdata,
                                rlib.R_ClassSymbol)
    if rlib.Rf_length(classes) == 0:
        dim = rlib.Rf_getAttrib(scaps._cdata,
                                rlib.R_DimSymbol)
        ndim = rlib.Rf_length(dim)
        if ndim > 0:
            if ndim == 2:
                classname  = 'matrix'
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
            _rinterface.rlib.Rf_allocVector(_rinterface.rlib.RAWSXP, n))
        _rinterface.ffi.memmove(
            _rinterface.rlib.RAW(cdata), state, n)
        ser = rmemory.protect(
            _rinterface.unserialize(cdata,
                                    embedded.globalenv.__sexp__._cdata)
        )
        res = _rinterface.SexpCapsule(ser)
    return res
