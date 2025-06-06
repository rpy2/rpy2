"""
R objects as Python objects.

The module is structured around the singleton r of class R,
that represents an embedded R.

License: GPLv2+

"""

import array
import contextlib
import os
import types
import typing
import warnings
import rpy2.rinterface as rinterface
import rpy2.rinterface_lib.embedded
import rpy2.rinterface_lib.openrlib
import rpy2.rlike.container as rlc

from rpy2.robjects.robject import RObjectMixin, RObject
import rpy2.robjects.functions
from rpy2.robjects.environments import (Environment,
                                        local_context)
from rpy2.robjects.methods import methods_env
from rpy2.robjects.methods import RS4

from . import conversion
from . import vectors
from . import language

from rpy2.rinterface import (Sexp,
                             SexpVector,
                             SexpClosure,
                             SexpEnvironment,
                             SexpS4,
                             StrSexpVector,
                             SexpExtPtr)

from rpy2.robjects.functions import Function
from rpy2.robjects.functions import SignatureTranslatedFunction

from rpy2.robjects.version import __version_vector__
from rpy2.robjects.version import __version__

_globalenv = rinterface.globalenv
_reval = rinterface.baseenv['eval']

BoolVector = vectors.BoolVector
IntVector = vectors.IntVector
FloatVector = vectors.FloatVector
ComplexVector = vectors.ComplexVector
StrVector = vectors.StrVector
FactorVector = vectors.FactorVector
Vector = vectors.Vector
PairlistVector = vectors.PairlistVector
ListVector = vectors.ListVector
DateVector = vectors.DateVector
POSIXct = vectors.POSIXct
POSIXlt = vectors.POSIXlt
Array = vectors.Array
Matrix = vectors.Matrix
DataFrame = vectors.DataFrame

# Missing values.
NA_Real = rinterface.NA_Real
NA_Integer = rinterface.NA_Integer
NA_Logical = rinterface.NA_Logical
NA_Character = rinterface.NA_Character
NA_Complex = rinterface.NA_Complex
NULL = rinterface.NULL


# TODO: Something like this could be part of the rpy2 API.
def _print_deferred_warnings() -> None:
    """Print R warning messages.

    rpy2's default pattern add a prefix per warning lines.
    This should be revised. In the meantime, we clean it
    at least for the R magic.
    """

    with rpy2.rinterface_lib.openrlib.rlock:
        rinterface.evalr('.Internal(printDeferredWarnings())')


def reval(string, envir=_globalenv):
    """ Evaluate a string as R code
    - string: a string
    - envir: an environment in which the environment should take place
             (default: R's global environment)
    """
    p = rinterface.parse(string)
    res = _reval(p, envir=envir)
    return res


default_converter = conversion.Converter('base empty converter')


@default_converter.rpy2py.register(RObject)
def _rpy2py_robject(obj):
    return obj


VT = typing.TypeVar('VT')
MT = typing.TypeVar('MT')
AT = typing.TypeVar('AT')


def _vector_matrix_array(
        obj, vector_cls: typing.Type[VT],
        matrix_cls: typing.Type[MT],
        array_cls: typing.Type[AT]) -> typing.Union[
            typing.Type[VT], typing.Type[MT], typing.Type[AT]]:
    # Should it be promoted to array or matrix ?
    try:
        dim = obj.do_slot("dim")
        if len(dim) == 2:
            return matrix_cls
        else:
            return array_cls
    except Exception:
        return vector_cls


@default_converter.rpy2py.register(rinterface.IntSexpVector)
def _convert_rpy2py_intvector(obj):
    clsmap = (conversion.converter_ctx.get()
              .rpy2py_nc_map[rinterface.IntSexpVector])
    cls = clsmap.find(obj.rclass)
    return cls(obj)


@default_converter.rpy2py.register(rinterface.FloatSexpVector)
def _convert_rpy2py_floatvector(obj):
    clsmap = (conversion.converter_ctx.get()
              .rpy2py_nc_map[rinterface.FloatSexpVector])
    cls = clsmap.find(obj.rclass)
    return cls(obj)


@default_converter.rpy2py.register(rinterface.ComplexSexpVector)
def _convert_rpy2py_complexvector(obj):
    clsmap = (conversion.converter_ctx.get()
              .rpy2py_nc_map[rinterface.ComplexSexpVector])
    cls = clsmap.find(obj.rclass)
    return cls(obj)


@default_converter.rpy2py.register(rinterface.BoolSexpVector)
def _convert_rpy2py_boolvector(obj):
    clsmap = (conversion.converter_ctx.get()
              .rpy2py_nc_map[rinterface.BoolSexpVector])
    cls = clsmap.find(obj.rclass)
    return cls(obj)


@default_converter.rpy2py.register(rinterface.StrSexpVector)
def _convert_rpy2py_strvector(obj):
    clsmap = (conversion.converter_ctx.get()
              .rpy2py_nc_map[rinterface.StrSexpVector])
    cls = clsmap.find(obj.rclass)
    return cls(obj)


@default_converter.rpy2py.register(rinterface.ByteSexpVector)
def _convert_rpy2py_bytevector(obj):
    clsmap = (conversion.converter_ctx.get()
              .rpy2py_nc_map[rinterface.ByteSexpVector])
    cls = clsmap.find(obj.rclass)
    return cls(obj)


default_converter.rpy2py.register(rinterface.PairlistSexpVector, PairlistVector)


@default_converter.rpy2py.register(rinterface.LangSexpVector)
def _convert_rpy2py_langvector(obj):
    if 'formula' in obj.rclass:
        cls = Formula
    else:
        cls = language.LangVector
    return cls(obj)


TYPEORDER = {bool: (0, BoolVector),
             int: (1, IntVector),
             float: (2, FloatVector),
             complex: (3, ComplexVector),
             str: (4, StrVector)}


def sequence_to_vector(lst):
    curr_typeorder = -1
    i = None
    for i, elt in enumerate(lst):
        cls = type(elt)
        if cls in TYPEORDER:
            if TYPEORDER[cls][0] > curr_typeorder:
                curr_typeorder, curr_type = TYPEORDER[cls]
        else:
            raise ValueError('The element %i in the list has a type '
                             'that cannot be handled.' % i)
    if i is None:
        raise ValueError('The parameter "lst" is an empty sequence. '
                         'The type of the corresponding R vector cannot '
                         'be determined.')
    res = curr_type(lst)
    return res


@default_converter.py2rpy.register(rinterface._MissingArgType)
def _py2rpy_missingargtype(obj):
    return obj


@default_converter.py2rpy.register(bool)
def _py2rpy_bool(obj):
    return obj


@default_converter.py2rpy.register(int)
def _py2rpy_int(obj):
    return obj


@default_converter.py2rpy.register(float)
def _py2rpy_float(obj):
    return obj


@default_converter.py2rpy.register(bytes)
def _py2rpy_bytes(obj):
    return obj


@default_converter.py2rpy.register(str)
def _py2rpy_str(obj):
    return obj


@default_converter.rpy2py.register(SexpClosure)
def _rpy2py_sexpclosure(obj):
    return SignatureTranslatedFunction(obj)


@default_converter.rpy2py.register(SexpEnvironment)
def _rpy2py_sexpenvironment(obj):
    return Environment(obj)


@default_converter.rpy2py.register(rinterface.ListSexpVector)
def _rpy2py_listsexp(obj):
    clsmap = (conversion.converter_ctx.get()
              .rpy2py_nc_map[rinterface.ListSexpVector])
    cls = clsmap.find(obj.rclass)
    return cls(obj)


@default_converter.rpy2py.register(SexpS4)
def _rpy2py_sexps4(obj):
    clsmap = (conversion.converter_ctx.get()
              .rpy2py_nc_map[SexpS4])
    cls = clsmap.find(methods_env['extends'](obj.rclass))
    return cls(obj)


@default_converter.rpy2py.register(SexpExtPtr)
def _rpy2py_sexpextptr(obj):
    clsmap = (conversion.converter_ctx.get()
              .rpy2py_nc_map[rinterface.SexpExtPtr])
    cls = clsmap.find(obj.rclass)
    return cls(obj)


@default_converter.rpy2py.register(object)
def _rpy2py_object(obj):
    return RObject(obj)


@default_converter.rpy2py.register(type(NULL))
def _rpy2py_null(obj):
    return obj


# TODO: delete ?
def default_py2ri(o):
    """ Convert an arbitrary Python object to a
    :class:`rpy2.rinterface.Sexp` object.
    Creates an R object with the content of the Python object,
    wich means data copying.
    :param o: object
    :rtype: :class:`rpy2.rinterface.Sexp` (and subclasses)
    """
    pass


@default_converter.py2rpy.register(RObject)
def _py2rpy_robject(obj):
    return rinterface.Sexp(obj)


@default_converter.py2rpy.register(Sexp)
def _py2rpy_sexp(obj):
    return obj


@default_converter.py2rpy.register(array.array)
def _py2rpy_array(obj):
    if obj.typecode in ('h', 'H', 'i', 'I'):
        res = IntVector(obj)
    elif obj.typecode in ('f', 'd'):
        res = FloatVector(obj)
    else:
        raise(
            ValueError('Nothing can be done for this array '
                       'type at the moment.')
        )
    return res


default_converter.py2rpy.register(int,
                                  lambda x: x)


@default_converter.py2rpy.register(list)
def _py2rpy_list(obj):
    cv = conversion.get_conversion()
    return vectors.ListVector(
        rinterface.ListSexpVector(
            [cv.py2rpy(x) for x in obj]
        )
    )


@default_converter.py2rpy.register(rlc.TaggedList)
def _py2rpy_taggedlist(obj):
    warnings.warn('TaggedList is deprecated. Use NamedList.',
                  DeprecationWarning)
    cv = conversion.get_conversion()
    res = vectors.ListVector(
        rinterface.ListSexpVector([cv.py2rpy(x) for x in obj])
    )
    res.do_slot_assign('names', rinterface.StrSexpVector(obj.tags))
    return res


@default_converter.py2rpy.register(rlc.NamedList)
def _py2rpy_namedlist(obj):
    cv = conversion.get_conversion()
    res = vectors.ListVector(
        rinterface.ListSexpVector([cv.py2rpy(x) for x in obj])
    )
    res.do_slot_assign('names', rinterface.StrSexpVector(tuple(obj.names())))
    return res


@default_converter.py2rpy.register(complex)
def _py2rpy_complex(obj):
    return obj


@default_converter.py2rpy.register(types.FunctionType)
def _function_to_rpy(func):
    def wrap(*args):
        res = func(*args)
        res = conversion.py2ro(res)
        return res
    rfunc = rinterface.rternalize(wrap)
    return conversion.get_conversion().rpy2py(rfunc)


@default_converter.rpy2py.register(object)
def _(obj):
    return obj


flatlist_converter = conversion.Converter('Converter to flatten/simplify lists')

# The default conversion for lists is currently to make them an R list. That
# has some advantages, but can be inconvenient (and, it's inconsistent with
# the way python lists are automatically converted by numpy functions), so
# for interactive use in the rmagic, we call unlist, which converts lists to
# vectors **if the list was of uniform (atomic) type**.
@flatlist_converter.py2rpy.register(list)
def flatlist_py2rpy_list(obj):
    # simplify2array is a utility function, but nice for us
    # TODO: use an early binding of the R function
    cv = conversion.get_conversion()
    robj = rinterface.ListSexpVector(
            [cv.py2rpy(x) for x in obj]
        )
    res = baseenv['simplify2array'](robj)
    # We need to ensure that a rpy2 objects is returned
    # This was issue #866 when this code in ipython-specific converter.
    res_rpy = cv.py2rpy(res)
    return res_rpy


class ExternalPointer(RObjectMixin, rinterface.SexpExtPtr):
    pass


default_converter._rpy2py_nc_map.update(
    {
        rinterface.SexpExtPtr: conversion.NameClassMap(ExternalPointer),
        rinterface.SexpS4: conversion.NameClassMap(RS4),
        rinterface.IntSexpVector: conversion.NameClassMap(
            lambda obj: _vector_matrix_array(
                obj, vectors.IntVector,
                vectors.IntMatrix, vectors.IntArray)(obj),
            {'factor': FactorVector}),
        rinterface.FloatSexpVector: conversion.NameClassMap(
            lambda obj: _vector_matrix_array(
                obj, vectors.FloatVector,
                vectors.FloatMatrix, vectors.FloatArray)(obj),
            {'Date': DateVector,
             'POSIXct': POSIXct}),
        rinterface.BoolSexpVector: conversion.NameClassMap(
            lambda obj: _vector_matrix_array(
                obj, vectors.BoolVector,
                vectors.BoolMatrix, vectors.BoolArray)(obj)
        ),
        rinterface.ByteSexpVector: conversion.NameClassMap(
            lambda obj: _vector_matrix_array(
                obj, vectors.ByteVector,
                vectors.ByteMatrix, vectors.ByteArray)(obj)
        ),
        rinterface.StrSexpVector: conversion.NameClassMap(
            lambda obj: _vector_matrix_array(
                obj, vectors.StrVector,
                vectors.StrMatrix, vectors.StrArray)(obj)
        ),
        rinterface.ComplexSexpVector: conversion.NameClassMap(
            lambda obj: _vector_matrix_array(obj, vectors.ComplexVector,
                                             vectors.ComplexMatrix, vectors.ComplexArray)(obj)
        ),
        rinterface.ListSexpVector: conversion.NameClassMap(
            ListVector,
            {'data.frame': DataFrame}),
        rinterface.SexpEnvironment: conversion.NameClassMap(Environment)
    }
)

class Formula(RObjectMixin, rinterface.Sexp):

    def __init__(self, formula, environment=_globalenv):
        if isinstance(formula, str):
            inpackage = rinterface.baseenv["::"]
            asformula = inpackage(rinterface.StrSexpVector(['stats', ]),
                                  rinterface.StrSexpVector(['as.formula', ]))
            formula = rinterface.StrSexpVector([formula, ])
            robj = asformula(formula,
                             env=environment)
        else:
            robj = formula
        super(Formula, self).__init__(robj)

    def getenvironment(self):
        """ Get the environment in which the formula is finding its symbols."""
        res = self.do_slot(".Environment")
        res = conversion.get_conversion().rpy2py(res)
        return res

    def setenvironment(self, val):
        """ Set the environment in which a formula will find its symbols."""
        if not isinstance(val, rinterface.SexpEnvironment):
            raise TypeError('The environment must be an instance of'
                            ' rpy2.rinterface.Sexp.environment')
        self.do_slot_assign('.Environment', val)

    environment = property(getenvironment, setenvironment, None,
                           'R environment in which the formula will look for '
                           'its variables.')


class R(object):
    """
    Singleton representing the embedded R running.
    """
    _instance = None
    # Default for the evaluation
    _print_r_warnings: bool = True
    _invisible: bool = True


    def __new__(cls):
        if cls._instance is None:
            rinterface.initr()
            cls._instance = object.__new__(cls)
        return cls._instance

    def __getattribute__(self, attr: str) -> object:
        try:
            return super(R, self).__getattribute__(attr)
        except AttributeError as ae:
            orig_ae = str(ae)

        try:
            return self.__getitem__(attr)
        except LookupError:
            raise AttributeError(orig_ae)

    def __getitem__(self, item: str) -> object:
        res = _globalenv.find(item)
        res = conversion.get_conversion().rpy2py(res)
        if hasattr(res, '__rname__'):
            res.__rname__ = item
        return res

    # TODO: check that this is properly working
    def __cleanup__(self) -> None:
        rinterface.embedded.endr(0)
        del(self)

    def __str__(self) -> str:
        s = [super(R, self).__str__()]
        version = self['version']
        version_k: typing.Tuple[str, ...] = tuple(version.names)  # type: ignore
        version_v: typing.Tuple[str, ...] = tuple(
            x[0] for x in version  # type: ignore
        )
        for key, val in zip(version_k, version_v):
            s.extend('%s: %s' % (key, val))
        return os.linesep.join(s)

    def __call__(self, string: str,
                 invisible: typing.Optional[bool] = None,
                 print_r_warnings: typing.Optional[bool] = None) -> object:
        """Evaluate a string as R code.

        :param string: A string with R code
        :param invisible: evaluate the R expression handling R's
          invisibility flag. When `True` expressions meant to return
          an "invisible" result (for example, `x <- 1`) will return
          None. The default is `None`, in which case the attribute
        _invisible is used.
        :param print_r_warning: When `True` the R deferred warnings
          are printed using the R callback function. The default is
          `None`, in which case the attribute _print_r_warning
          is used.
        :return: The value returned by R after rpy2 conversion."""
        r_expr = rinterface.parse(string)
        if invisible is None:
            invisible = self._invisible
        if invisible:
            res, visible = rinterface.evalr_expr_with_visible(   # type: ignore
                r_expr
            )
            if not visible[0]:  # type: ignore
                res = None
        else:
            res = rinterface.evalr_expr(r_expr)
        if print_r_warnings is None:
            print_r_warnings = self._print_r_warnings
        if print_r_warnings:
            _print_deferred_warnings()
        return (None if res is None
                else conversion.get_conversion().rpy2py(res))


r = R()
rl = language.LangVector.from_string

conversion.set_conversion(default_converter)

globalenv = conversion.converter_ctx.get().rpy2py(_globalenv)
baseenv = conversion.converter_ctx.get().rpy2py(rinterface.baseenv)
emptyenv = conversion.converter_ctx.get().rpy2py(rinterface.emptyenv)
