"""
R objects as Python objects.

The module is structured around the singleton r of class R,
that represents an embedded R.

License: GPLv2+

"""

import array
import contextlib
import os
from functools import partial
import types
import rpy2.rinterface as rinterface
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


def _vector_matrix_array(obj, vector_cls, matrix_cls, array_cls):
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
    clsmap = conversion.converter.rpy2py_nc_name[rinterface.IntSexpVector]
    cls = clsmap.find(obj.rclass)
    return cls(obj)


@default_converter.rpy2py.register(rinterface.FloatSexpVector)
def _convert_rpy2py_floatvector(obj):
    clsmap = conversion.converter.rpy2py_nc_name[rinterface.FloatSexpVector]
    cls = clsmap.find(obj.rclass)
    return cls(obj)


@default_converter.rpy2py.register(rinterface.ComplexSexpVector)
def _convert_rpy2py_complexvector(obj):
    clsmap = conversion.converter.rpy2py_nc_name[rinterface.ComplexSexpVector]
    cls = clsmap.find(obj.rclass)
    return cls(obj)


@default_converter.rpy2py.register(rinterface.BoolSexpVector)
def _convert_rpy2py_boolvector(obj):
    clsmap = conversion.converter.rpy2py_nc_name[rinterface.BoolSexpVector]
    cls = clsmap.find(obj.rclass)
    return cls(obj)


@default_converter.rpy2py.register(rinterface.StrSexpVector)
def _convert_rpy2py_strvector(obj):    
    cls = _vector_matrix_array(obj, vectors.StrVector,
                               vectors.StrMatrix, vectors.StrArray)
    return cls(obj)


@default_converter.rpy2py.register(rinterface.ByteSexpVector)
def _convert_rpy2py_bytevector(obj):
    cls = _vector_matrix_array(obj, vectors.ByteVector,
                               vectors.ByteMatrix, vectors.ByteArray)
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
    clsmap = conversion.converter.rpy2py_nc_name[rinterface.ListSexpVector]
    cls = clsmap.find(obj.rclass)
    return cls(obj)


@default_converter.rpy2py.register(SexpS4)
def _rpy2py_sexps4(obj):
    clsmap = conversion.converter.rpy2py_nc_name[SexpS4]
    cls = clsmap.find(methods_env['extends'](obj.rclass))
    return cls(obj)


@default_converter.rpy2py.register(SexpExtPtr)
def _rpy2py_sexpextptr(obj):
    return obj


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
    return vectors.ListVector(
        rinterface.ListSexpVector(
            [conversion.py2rpy(x) for x in obj]
        )
    )


@default_converter.py2rpy.register(rlc.TaggedList)
def _py2rpy_taggedlist(obj):
    res = vectors.ListVector(
        rinterface.ListSexpVector([conversion.py2rpy(x) for x in obj])
    )
    res.do_slot_assign('names', rinterface.StrSexpVector(obj.tags))
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
    return conversion.rpy2py(rfunc)


@default_converter.rpy2py.register(object)
def _(obj):
    return obj


default_converter._rpy2py_nc_map.update(
    {
        rinterface.SexpS4: conversion.NameClassMap(RS4),
        rinterface.IntSexpVector: conversion.NameClassMap(
            lambda obj: _vector_matrix_array(obj, vectors.IntVector,
                                             vectors.IntMatrix, vectors.IntArray)(obj),
            {'factor': FactorVector}),
        rinterface.FloatSexpVector: conversion.NameClassMap(
            lambda obj: _vector_matrix_array(obj, vectors.FloatVector,
                                             vectors.FloatMatrix, vectors.FloatArray)(obj),
            {'Date': DateVector,
             'POSIXct': POSIXct}),
        rinterface.BoolSexpVector: conversion.NameClassMap(
            lambda obj: _vector_matrix_array(obj, vectors.BoolVector,
                                             vectors.BoolMatrix, vectors.BoolArray)(obj)
        ),
        rinterface.ByteSexpVector: conversion.NameClassMap(
            lambda obj: _vector_matrix_array(obj, vectors.ByteVector,
                                             vectors.ByteMatrix, vectors.ByteArray)(obj)
        ),
        rinterface.StrSexpVector: conversion.NameClassMap(
            lambda obj: _vector_matrix_array(obj, vectors.StrVector,
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
        res = conversion.rpy2py(res)
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

    def __new__(cls):
        if cls._instance is None:
            rinterface.initr_simple()
            cls._instance = object.__new__(cls)
        return cls._instance

    def __getattribute__(self, attr):
        try:
            return super(R, self).__getattribute__(attr)
        except AttributeError as ae:
            orig_ae = str(ae)

        try:
            return self.__getitem__(attr)
        except LookupError:
            raise AttributeError(orig_ae)

    def __getitem__(self, item):
        res = _globalenv.find(item)
        res = conversion.rpy2py(res)
        if hasattr(res, '__rname__'):
            res.__rname__ = item
        return res

    # TODO: check that this is properly working
    def __cleanup__(self):
        rinterface.embedded.endr(0)
        del(self)

    def __str__(self):
        version = self['version']
        s = [super(R, self).__str__()]
        s.extend('%s: %s' % (n, val[0])
                 for n, val in zip(version.names, version))
        return os.linesep.join(s)

    def __call__(self, string):
        p = rinterface.parse(string)
        res = self.eval(p)
        return conversion.rpy2py(res)


r = R()
rl = language.LangVector.from_string

conversion.set_conversion(default_converter)

globalenv = conversion.converter.rpy2py(_globalenv)
baseenv = conversion.converter.rpy2py(rinterface.baseenv)
emptyenv = conversion.converter.rpy2py(rinterface.emptyenv)
