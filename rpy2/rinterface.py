import atexit
import contextlib
import os
import math
import platform
import signal
import textwrap
import threading
import typing
import warnings
from typing import Union
from rpy2.rinterface_lib import openrlib
import rpy2.rinterface_lib._rinterface_capi as _rinterface
import rpy2.rinterface_lib.embedded as embedded
import rpy2.rinterface_lib.conversion as conversion
from rpy2.rinterface_lib.conversion import _cdata_res_to_rinterface
import rpy2.rinterface_lib.memorymanagement as memorymanagement
from rpy2.rinterface_lib import na_values
from rpy2.rinterface_lib.sexp import NULLType
import rpy2.rinterface_lib.bufferprotocol as bufferprotocol
from rpy2.rinterface_lib import sexp
from rpy2.rinterface_lib.sexp import CharSexp  # noqa: F401
from rpy2.rinterface_lib.sexp import RTYPES
from rpy2.rinterface_lib.sexp import SexpVector
from rpy2.rinterface_lib.sexp import StrSexpVector
from rpy2.rinterface_lib.sexp import Sexp
from rpy2.rinterface_lib.sexp import SexpEnvironment
from rpy2.rinterface_lib.sexp import unserialize  # noqa: F401
from rpy2.rinterface_lib.sexp import emptyenv
from rpy2.rinterface_lib.sexp import baseenv
from rpy2.rinterface_lib.sexp import globalenv

if os.name == 'nt':
    import rpy2.rinterface_lib.embedded_mswin as embedded_mswin
    embedded._initr = embedded_mswin._initr_win32

R_NilValue = openrlib.rlib.R_NilValue

endr = embedded.endr

_evaluation_context = globalenv


def get_evaluation_context() -> SexpEnvironment:
    """Get the frame (environment) in which R code is currently evaluated."""
    return _evaluation_context


@contextlib.contextmanager
def local_context(
        env: typing.Optional[SexpEnvironment] = None,
        use_rlock: bool = True
) -> typing.Iterator[SexpEnvironment]:
    """Local context for the evaluation of R code.

    Args:
    - env: an environment to use as a context. If not specified (None, the
      default), a child environment to the current context is created.
    - use_rlock: whether to use a threading lock (see the documentation about
      "rlock". The default is True.

    Returns:
    Yield the environment (passed to env, or created).
    """

    global _evaluation_context

    parent_frame = _evaluation_context
    if env is None:
        env = baseenv['new.env'](
            baseenv['parent.frame']()
            if parent_frame is None
            else parent_frame)
    try:
        if use_rlock:
            with openrlib.rlock:
                _evaluation_context = env
                yield env
        else:
            _evaluation_context = env
            yield env
    finally:
        _evaluation_context = parent_frame


def _sigint_handler(sig, frame):
    raise KeyboardInterrupt()


@_cdata_res_to_rinterface
def parse(text: str, num: int = -1):
    """Parse a string as R code.

    :param:`text` A string with R code to parse.
    :param:`num` The maximum number of lines to parse. If -1, no
      limit is applied.
    """

    if not isinstance(text, str):
        raise TypeError('text must be a string.')
    robj = StrSexpVector([text])
    with memorymanagement.rmemory() as rmemory:
        res = _rinterface._parse(robj.__sexp__._cdata, num, rmemory)
    return res


def evalr(source: str, maxlines: int = -1) -> sexp.Sexp:
    """Evaluate a string as R code.

    Evaluate a string as R just as it would happen when writing
    code in an R terminal.

    :param:`text` A string to be evaluated as R code.
    :param:`maxlines` The maximum number of lines to parse. If -1, no
      limit is applied."""

    res = parse(source, num=maxlines)
    res = baseenv['eval'](res)
    return res


def vector_memoryview(obj: sexp.SexpVector,
                      sizeof_str: str, cast_str: str) -> memoryview:
    """
    :param:`obj` R vector
    :param:`sizeof_str` Type in a string to use with ffi.sizeof()
        (for example "int")
    :param:`cast_str` Type in a string to use with memoryview.cast()
        (for example "i")
    """
    b = openrlib.ffi.buffer(
        obj._R_GET_PTR(obj.__sexp__._cdata),
        openrlib.ffi.sizeof(sizeof_str) * len(obj))
    shape = bufferprotocol.getshape(obj.__sexp__._cdata)
    # One could have expected to only need builtin Python
    # and do something like
    # ```
    # mv = memoryview(b).cast(cast_str, shape, order='F')
    # ```
    # but Python does not handle FORTRAN-ordered arrays without having
    # to write C extensions. We have to use numpy.
    # TODO: Having numpy a requirement just for this is a problem.
    # TODO: numpy needed for memoryview
    #   (as long as https://bugs.python.org/issue34778 not resolved)
    import numpy
    a = numpy.frombuffer(b, dtype=cast_str).reshape(shape, order='F')
    mv = memoryview(a)
    return mv


class SexpSymbol(sexp.Sexp):
    """An unevaluated R symbol."""

    def __init__(
            self,
            obj: Union[Sexp,
                       _rinterface.SexpCapsule,
                       _rinterface.UninitializedRCapsule,
                       str]
    ):
        if isinstance(obj, Sexp) or isinstance(obj, _rinterface.CapsuleBase):
            super().__init__(obj)
        elif isinstance(obj, str):
            name_cdata = _rinterface.ffi.new('char []', obj.encode('utf-8'))
            sexp = _rinterface.SexpCapsule(
                openrlib.rlib.Rf_install(name_cdata))
            super().__init__(sexp)
        else:
            raise TypeError(
                'The constructor must be called '
                'with that is an instance of rpy2.rinterface.sexp.Sexp '
                'or an instance of rpy2.rinterface._rinterface.SexpCapsule')

    def __str__(self) -> str:
        return conversion._cchar_to_str(
            openrlib._STRING_VALUE(
                self._sexpobject._cdata
            ), 'utf-8'
        )


class _MissingArgType(SexpSymbol, metaclass=sexp.SingletonABC):

    def __init__(self):
        if embedded.isready():
            tmp = sexp.Sexp(
                _rinterface.UnmanagedSexpCapsule(
                    openrlib.rlib.R_MissingArg
                )
            )
        else:
            tmp = sexp.Sexp(
                _rinterface.UninitializedRCapsule(RTYPES.SYMSXP.value)
            )
        super().__init__(tmp)

    def __bool__(self) -> bool:
        """This is always False."""
        return False

    @property
    def __sexp__(self) -> _rinterface.SexpCapsule:
        return self._sexpobject


MissingArg = _MissingArgType()


class SexpPromise(Sexp):

    @_cdata_res_to_rinterface
    def eval(self, env: typing.Optional[SexpEnvironment] = None) -> sexp.Sexp:
        """"Evalute the R "promise".

        :param:`env` The environment in which to evaluate the
          promise.
        """
        if env is None:
            env = globalenv
        return openrlib.rlib.Rf_eval(self.__sexp__._cdata, env)


NPCOMPAT_TYPE = typing.TypeVar('NPCOMPAT_TYPE',
                               'ByteSexpVector',
                               'BoolSexpVector',
                               'IntSexpVector',
                               'FloatSexpVector')


class NumpyArrayMixin:
    """Numpy-specific API for accessing the content of a numpy array.

    This interface implements version 3 of Numpy's `__array_interface__`
    and is only available / possible for some of the R vectors."""

    @property
    def __array_interface__(
            self: NPCOMPAT_TYPE
    ) -> dict:
        """Return an `__array_interface__` version 3.

        Note that the pointer returned in the items 'data' corresponds to
        a memory area under R's memory management and that it will become
        invalid once the area once R frees the object. It is safer to keep
        the rpy2 object proxying the R object alive for the duration the
        pointer is used in Python / numpy."""
        shape = bufferprotocol.getshape(self.__sexp__._cdata)
        data = openrlib.ffi.buffer(self._R_GET_PTR(self.__sexp__._cdata))
        strides = bufferprotocol.getstrides(self.__sexp__._cdata,
                                            shape,
                                            self._R_SIZEOF_ELT)
        return {'shape': shape,
                'typestr': self._NP_TYPESTR,
                'strides': strides,
                'data': data,
                'version': 3}


class ByteSexpVector(NumpyArrayMixin, SexpVector):
    """Array of bytes.

    This is the R equivalent to a Python :class:`bytesarray`.
    """

    _R_TYPE = openrlib.rlib.RAWSXP
    _R_SIZEOF_ELT = _rinterface.ffi.sizeof('char')
    _NP_TYPESTR = '|u1'

    _R_GET_PTR = staticmethod(openrlib.RAW)

    @staticmethod
    def _CAST_IN(x: typing.Any) -> int:
        if isinstance(x, int):
            if x > 255:
                raise ValueError('byte must be in range(0, 256)')
            res = x
        elif isinstance(x, (bytes, bytearray)):
            if len(x) != 1:
                raise ValueError('byte must be a single character')
            res = ord(x)
        else:
            raise ValueError('byte must be an integer [0, 255] or a '
                             'single byte character')
        return res

    @staticmethod
    def _R_VECTOR_ELT(x, i: int) -> None:
        return openrlib.RAW(x)[i]

    @staticmethod
    def _R_SET_VECTOR_ELT(x, i: int, val) -> None:
        openrlib.RAW(x)[i] = val

    def __getitem__(self,
                    i: Union[int, slice]) -> Union[int, 'ByteSexpVector']:

        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            res = openrlib.RAW_ELT(cdata, i_c)
        elif isinstance(i, slice):
            res = type(self).from_iterable(
                [openrlib.RAW_ELT(
                    cdata, i_c
                ) for i_c in range(*i.indices(len(self)))
                ]
            )
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))
        return res

    def __setitem__(self, i: Union[int, slice], value) -> None:
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            openrlib.RAW(cdata)[i_c] = self._CAST_IN(value)
        elif isinstance(i, slice):
            for i_c, v in zip(range(*i.indices(len(self))), value):
                if v > 255:
                    raise ValueError('byte must be in range(0, 256)')
                openrlib.RAW(cdata)[i_c] = self._CAST_IN(v)
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))


class BoolSexpVector(NumpyArrayMixin, SexpVector):
    """Array of booleans.

    Note that R is internally storing booleans as integers to
    allow an additional "NA" value to represent missingness."""

    _R_TYPE = openrlib.rlib.LGLSXP
    _R_SIZEOF_ELT = _rinterface.ffi.sizeof('Rboolean')
    _NP_TYPESTR = '|i'
    _R_VECTOR_ELT = openrlib.LOGICAL_ELT
    _R_SET_VECTOR_ELT = openrlib.SET_LOGICAL_ELT
    _R_GET_PTR = staticmethod(openrlib.LOGICAL)

    @staticmethod
    def _CAST_IN(x):
        if x is None or x == openrlib.rlib.R_NaInt:
            return NA_Logical
        else:
            return bool(x)

    def __getitem__(self, i: Union[int, slice]) -> Union[typing.Optional[bool],
                                                         'BoolSexpVector']:
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            elt = openrlib.LOGICAL_ELT(cdata, i_c)
            res = na_values.NA_Logical if elt == NA_Logical else bool(elt)
        elif isinstance(i, slice):
            res = type(self).from_iterable(
                [openrlib.LOGICAL_ELT(cdata, i_c)
                 for i_c in range(*i.indices(len(self)))]
            )
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))
        return res

    def __setitem__(self, i: Union[int, slice], value) -> None:
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            openrlib.SET_LOGICAL_ELT(cdata, i_c,
                                     int(value))
        elif isinstance(i, slice):
            for i_c, v in zip(range(*i.indices(len(self))), value):
                openrlib.SET_LOGICAL_ELT(cdata, i_c,
                                         int(v))
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))

    def memoryview(self) -> memoryview:
        return vector_memoryview(self, 'int', 'i')


def nullable_int(v):
    if type(v) is float and math.isnan(v):
        return openrlib.rlib.R_NaInt
    else:
        return int(v)


class IntSexpVector(NumpyArrayMixin, SexpVector):

    _R_TYPE = openrlib.rlib.INTSXP
    _R_SET_VECTOR_ELT = openrlib.SET_INTEGER_ELT
    _R_VECTOR_ELT = openrlib.INTEGER_ELT
    _R_SIZEOF_ELT = _rinterface.ffi.sizeof('int')
    _NP_TYPESTR = '|i'

    _R_GET_PTR = staticmethod(openrlib.INTEGER)
    _CAST_IN = staticmethod(nullable_int)

    def __getitem__(self, i: Union[int, slice]) -> Union[int, 'IntSexpVector']:
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            res = openrlib.INTEGER_ELT(cdata, i_c)
            if res == NA_Integer:
                res = NA_Integer
        elif isinstance(i, slice):
            res = type(self).from_iterable(
                [openrlib.INTEGER_ELT(
                    cdata, i_c
                ) for i_c in range(*i.indices(len(self)))]
            )
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))
        return res

    def __setitem__(self, i: Union[int, slice], value) -> None:
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
        return vector_memoryview(self, 'int', 'i')


class FloatSexpVector(NumpyArrayMixin, SexpVector):

    _R_TYPE = openrlib.rlib.REALSXP
    _R_VECTOR_ELT = openrlib.REAL_ELT
    _R_SET_VECTOR_ELT = openrlib.SET_REAL_ELT
    _R_SIZEOF_ELT = _rinterface.ffi.sizeof('double')
    _NP_TYPESTR = '|d'

    _CAST_IN = staticmethod(float)
    _R_GET_PTR = staticmethod(openrlib.REAL)

    def __getitem__(
            self, i: Union[int, slice]
    ) -> Union[float, 'FloatSexpVector']:
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            res = openrlib.REAL_ELT(cdata, i_c)
        elif isinstance(i, slice):
            res = type(self).from_iterable(
                [openrlib.REAL_ELT(
                    cdata, i_c) for i_c in range(*i.indices(len(self)))]
            )
        else:
            raise TypeError('Indices must be integers or slices, not %s' %
                            type(i))
        return res

    def __setitem__(self, i: Union[int, slice], value) -> None:
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
        return vector_memoryview(self, 'double', 'd')


class ComplexSexpVector(SexpVector):

    _R_TYPE = openrlib.rlib.CPLXSXP
    _R_GET_PTR = staticmethod(openrlib.COMPLEX)
    _R_SIZEOF_ELT = _rinterface.ffi.sizeof('Rcomplex')

    @staticmethod
    def _R_VECTOR_ELT(x, i):
        return openrlib.COMPLEX(x)[i]

    @staticmethod
    def _R_SET_VECTOR_ELT(x, i, v):
        openrlib.COMPLEX(x).__setitem__(i, v)

    @staticmethod
    def _CAST_IN(x):
        if isinstance(x, complex):
            res = (x.real, x.imag)
        else:
            try:
                res = (x.r, x.i)
            except AttributeError:
                raise TypeError(
                    'Unable to turn value into an R complex number.'
                )
        return res

    def __getitem__(
            self, i: Union[int, slice]
    ) -> Union[complex, 'ComplexSexpVector']:
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            _ = openrlib.COMPLEX_ELT(cdata, i_c)
            res = complex(_.r, _.i)
        elif isinstance(i, slice):
            res = type(self).from_iterable(
                [openrlib.COMPLEX_ELT(
                    cdata, i_c) for i_c in range(*i.indices(len(self)))]
            )
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))
        return res

    def __setitem__(self, i: Union[int, slice], value) -> None:
        cdata = self.__sexp__._cdata
        if isinstance(i, int):
            i_c = _rinterface._python_index_to_c(cdata, i)
            openrlib.COMPLEX(cdata)[i_c] = self._CAST_IN(value)
        elif isinstance(i, slice):
            for i_c, v in zip(range(*i.indices(len(self))), value):
                openrlib.COMPLEX(cdata)[i_c] = self._CAST_IN(v)
        else:
            raise TypeError(
                'Indices must be integers or slices, not %s' % type(i))


class ListSexpVector(SexpVector):
    """R list.

    An R list an R vector (array) that is similar to a Python list in
    the sense that items in the list can be of any type, whereas most
    other R vectors are homogeneous (all items are of the same type).
    """
    _R_TYPE = openrlib.rlib.VECSXP
    _R_GET_PTR = staticmethod(openrlib._VECTOR_PTR)
    _R_SIZEOF_ELT = None
    _R_VECTOR_ELT = openrlib.rlib.VECTOR_ELT
    _R_SET_VECTOR_ELT = openrlib.rlib.SET_VECTOR_ELT
    _CAST_IN = staticmethod(conversion._get_cdata)


class PairlistSexpVector(SexpVector):
    """R pairlist.

    A R pairlist is rarely used outside of R's internal libraries and
    a relatively small number of use cases. It is essentially a LISP-like
    list of (name, value) pairs.
    """
    _R_TYPE = openrlib.rlib.LISTSXP
    _R_GET_PTR = None
    _R_SIZEOF_ELT = None
    _R_VECTOR_ELT = None
    _R_SET_VECTOR_ELT = None
    _CAST_IN = staticmethod(conversion._get_cdata)

    def __getitem__(self, i: Union[int, slice]) -> Sexp:
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
                item_cdata_name = rlib.PRINTNAME(rlib.TAG(item_cdata))
                if _rinterface._TYPEOF(item_cdata_name) != rlib.NILSXP:
                    rlib.SET_STRING_ELT(
                        res_name,
                        0,
                        item_cdata_name)
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
    _R_SIZEOF_ELT = None
    _R_VECTOR_ELT = openrlib.rlib.VECTOR_ELT
    _R_SET_VECTOR_ELT = None


class LangSexpVector(SexpVector):
    _R_TYPE = openrlib.rlib.LANGSXP
    _R_GET_PTR = None
    _CAST_IN = None
    _R_SIZEOF_ELT = None
    _R_VECTOR_ELT = None
    _R_SET_VECTOR_ELT = None

    @_cdata_res_to_rinterface
    def __getitem__(self, i: int):
        cdata = self.__sexp__._cdata
        i_c = _rinterface._python_index_to_c(cdata, i)
        return openrlib.rlib.CAR(
            openrlib.rlib.Rf_nthcdr(cdata, i_c)
        )

    def __setitem__(self, i: int, value: sexp.SupportsSEXP) -> None:
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
            call_context = _evaluation_context
            res = rmemory.protect(
                openrlib.rlib.R_tryEval(
                    call_r,
                    call_context.__sexp__._cdata,
                    error_occured)
            )
            if error_occured[0]:
                raise embedded.RRuntimeError(_rinterface._geterrmessage())
        return res

    @_cdata_res_to_rinterface
    def rcall(self, keyvals,
              environment: typing.Optional[SexpEnvironment] = None):
        """Call/evaluate an R function.

        Args:
        - keyvals: a sequence of key/value (name/parameter) pairs. A
          name/parameter that is None will indicated an unnamed parameter.
          Like in R, keys/names do not have to be unique, partial matching
          can be used, and named/unnamed parameters can occur at any position
          in the sequence.
        - environment: an optional R environment to evaluate the function.
        """
        # TODO: check keyvals are pairs ?
        if environment is None:
            environment = _evaluation_context
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
            (_rinterface._capsule_finalizer_c
             if _rinterface._capsule_finalizer_c
             else _rinterface._capsule_finalizer))
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
    float: conversion._float_to_sexp,
    complex: conversion._complex_to_sexp
    })

conversion._PY_R_MAP.update({
    _rinterface.ffi.CData: False,
    # integer
    int: conversion._int_to_sexp,
    sexp.NAIntegerType: conversion._int_to_sexp,
    # float
    float: conversion._float_to_sexp,
    sexp.NARealType: conversion._float_to_sexp,
    # boolean
    bool: conversion._bool_to_sexp,
    sexp.NALogicalType: conversion._bool_to_sexp,
    # string
    str: conversion._str_to_sexp,
    sexp.CharSexp: None,
    sexp.NACharacterType: None,
    # complex
    complex: conversion._complex_to_sexp,
    sexp.NAComplexType: conversion._complex_to_sexp,
    # None
    type(None): lambda x: openrlib.rlib.R_NilValue})


def vector(iterable, rtype: RTYPES) -> SexpVector:
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


NULL = None
MissingArg = _MissingArgType()
NA_Character = None
NA_Integer = None
NA_Logical = None
NA = None
NA_Real = None
NA_Complex = None


def initr_simple() -> typing.Optional[int]:
    """Initialize R's embedded C library."""
    with openrlib.rlock:
        status = embedded._initr()
        atexit.register(endr, 0)
        _rinterface._register_external_symbols()
        _post_initr_setup()
        return status


def initr_checkenv() -> typing.Optional[int]:
    # Force the internal initialization flag if there is an environment
    # variable that indicates that R was already initialized in the current
    # process.

    status = None
    with openrlib.rlock:
        if embedded.is_r_externally_initialized():
            embedded._setinitialized()
        else:
            status = embedded._initr()
            embedded.set_python_process_info()
        _rinterface._register_external_symbols()
        _post_initr_setup()
    return status


initr = initr_checkenv


def _update_R_ENC_PY():
    conversion._R_ENC_PY[openrlib.rlib.CE_UTF8] = 'utf-8'

    l10n_info = tuple(baseenv['l10n_info']())
    if platform.system() == 'Windows':
        val_latin1 = 'cp{:d}'.format(l10n_info[3][0])
    else:
        val_latin1 = 'latin1'
    conversion._R_ENC_PY[openrlib.rlib.CE_LATIN1] = val_latin1

    if l10n_info[1]:
        val_native = conversion._R_ENC_PY[openrlib.rlib.CE_UTF8]
    else:
        val_native = val_latin1
    conversion._R_ENC_PY[openrlib.rlib.CE_NATIVE] = val_native

    conversion._R_ENC_PY[openrlib.rlib.CE_ANY] = 'utf-8'


def _post_initr_setup() -> None:

    emptyenv.__sexp__ = _rinterface.SexpCapsule(openrlib.rlib.R_EmptyEnv)
    baseenv.__sexp__ = _rinterface.SexpCapsule(openrlib.rlib.R_BaseEnv)
    globalenv.__sexp__ = _rinterface.SexpCapsule(openrlib.rlib.R_GlobalEnv)

    global NULL
    NULL = NULLType()

    MissingArg._sexpobject = _rinterface.UnmanagedSexpCapsule(
        openrlib.rlib.R_MissingArg
    )

    global NA_Character
    na_values.NA_Character = sexp.NACharacterType()
    NA_Character = na_values.NA_Character

    global NA_Integer
    na_values.NA_Integer = sexp.NAIntegerType(openrlib.rlib.R_NaInt)
    NA_Integer = na_values.NA_Integer

    global NA_Logical, NA
    na_values.NA_Logical = sexp.NALogicalType(openrlib.rlib.R_NaInt)
    NA_Logical = na_values.NA_Logical
    NA = NA_Logical

    global NA_Real
    na_values.NA_Real = sexp.NARealType(openrlib.rlib.R_NaReal)
    NA_Real = na_values.NA_Real

    global NA_Complex
    na_values.NA_Complex = sexp.NAComplexType(
        _rinterface.ffi.new(
            'Rcomplex *',
            [openrlib.rlib.R_NaReal, openrlib.rlib.R_NaReal])
    )
    NA_Complex = na_values.NA_Complex

    warn_about_thread = False
    if threading.current_thread() is threading.main_thread():
        try:
            signal.signal(signal.SIGINT, _sigint_handler)
        except ValueError as ve:
            if str(ve) == 'signal only works in main thread':
                warn_about_thread = True
            else:
                raise ve
    else:
        warn_about_thread = True
    if warn_about_thread:
        warnings.warn(
            textwrap.dedent(
                """R is not initialized by the main thread.
                Its taking over SIGINT cannot be reversed here, and as a
                consequence the embedded R cannot be interrupted with Ctrl-C.
                Consider (re)setting the signal handler of your choice from
                the main thread."""
            )
        )

    _update_R_ENC_PY()


def rternalize(function: typing.Callable) -> SexpClosure:
    """ Make a Python function callable from R.

    Takes an arbitrary Python function and wrap it in such a way that
    it can be called from the R side.

    :param function: A Python callable object.
    :return: A wrapped R object that can be use like any other rpy2
    object.
    """

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


def process_revents() -> None:
    """Process R events.

    Calling this function a regular interval can help ensure that
    R is processing input events (e.g., resizing of a window with
    graphics)."""
    openrlib.rlib.rpy2_runHandlers(openrlib.rlib.R_InputHandlers)
