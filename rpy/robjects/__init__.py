"""
R objects as Python objects.

The module is structured around the singleton r of class R,
that represents an embedded R.

License: GPLv3.0 (although a dual license can be worked out)

"""

import os, sys
import array
import itertools
import rpy2.rinterface as rinterface
import rpy2.rlike.container as rlc

import conversion

from rpy2.robjects.robject import RObjectMixin, RObject
from rpy2.robjects.methods import RS4
from rpy2.robjects.vectors import *
from rpy2.robjects.functions import Function, SignatureTranslatedFunction

_parse = rinterface.baseenv['parse']
_reval = rinterface.baseenv['eval']
# missing values
NA_real = _reval(_parse(text = rinterface.StrSexpVector(("NA_real_", ))))
NA_integer = _reval(_parse(text = rinterface.StrSexpVector(("NA_integer_", ))))
NA_bool = _reval(_parse(text = rinterface.StrSexpVector(("NA", ))))
NA_character = _reval(_parse(text = rinterface.StrSexpVector(("NA_character_", ))))
NA_complex = _reval(_parse(text = rinterface.StrSexpVector(("NA_complex_", ))))
# NULL
NULL = _reval(_parse(text = rinterface.StrSexpVector(("NULL", ))))
# TRUE/FALSE
TRUE = _reval(_parse(text = rinterface.StrSexpVector(("TRUE", ))))
FALSE = _reval(_parse(text = rinterface.StrSexpVector(("FALSE", ))))



#FIXME: close everything when leaving (check RPy for that).


def default_ri2py(o):
    """ Convert :class:`rpy2.rinterface.Sexp` to higher-level objects,
    without copying the R objects.

    :param o: object
    :rtype: :class:`rpy2.robjects.RObject (and subclasses)`
    """

    res = None
    try:
        rcls = o.do_slot("class")[0]
    except LookupError, le:
        rcls = None

    if isinstance(o, RObject):
        res = o
    elif isinstance(o, rinterface.SexpVector):
        if rcls == 'data.frame':
            res = vectors.DataFrame(o)
        if res is None:
            try:
                dim = o.do_slot("dim")
                if len(dim) == 2:
                    res = vectors.Matrix(o)
                else:
                    res = vectors.Array(o)
            except LookupError, le:
                if o.typeof == rinterface.INTSXP:
                    if rcls == 'factor':
                        res = vectors.FactorVector(o)
                    else:
                        res = vectors.IntVector(o)
                elif o.typeof == rinterface.REALSXP:
                    res = vectors.FloatVector(o)
                elif o.typeof == rinterface.STRSXP:
                    res = vectors.StrVector(o)
                elif o.typeof == rinterface.LANGSXP and rcls == 'formula':
                    res = Formula(o)
                else:
                    res = vectors.Vector(o)

    elif isinstance(o, rinterface.SexpClosure):
        res = SignatureTranslatedFunction(o)
    elif isinstance(o, rinterface.SexpEnvironment):
        res = Environment(o)
    elif isinstance(o, rinterface.SexpS4):
        res = RS4(o)
    else:
        res = RObject(o)
    return res

conversion.ri2py = default_ri2py


def default_py2ri(o):
    """ Convert arbitrary Python object to :class:`rpy2.rinterface.Sexp` to objects,
    creating an R object with the content of the Python object in the process
    (wich means data copying).

    :param o: object
    :rtype: :class:`rpy2.rinterface.Sexp` (and subclasses)

    """
    if isinstance(o, RObject):
        res = rinterface.Sexp(o)
    if isinstance(o, rinterface.Sexp):
        res = o
    elif isinstance(o, array.array):
        if o.typecode in ('h', 'H', 'i', 'I'):
            res = rinterface.SexpVector(o, rinterface.INTSXP)
        elif o.typecode in ('f', 'd'):
            res = rinterface.SexpVector(o, rinterface.REALSXP)
        else:
            raise(ValueError("Nothing can be done for this array type at the moment."))
    elif isinstance(o, bool):
        res = rinterface.SexpVector([o, ], rinterface.LGLSXP)
    elif isinstance(o, int) or isinstance(o, long):
        res = rinterface.SexpVector([o, ], rinterface.INTSXP)
    elif isinstance(o, float):
        res = rinterface.SexpVector([o, ], rinterface.REALSXP)
    elif isinstance(o, str):
        res = rinterface.SexpVector([o, ], rinterface.STRSXP)
    elif isinstance(o, unicode):
        res = rinterface.SexpVector([o, ], rinterface.STRSXP)
    elif isinstance(o, list):
        res = r.list(*[conversion.ri2py(conversion.py2ri(x)) for x in o])
    elif isinstance(o, complex):
        res = rinterface.SexpVector([o, ], rinterface.CPLXSXP)
    else:
        raise(ValueError("Nothing can be done for the type %s at the moment." %(type(o))))
    return res

conversion.py2ri = default_py2ri


def default_py2ro(o):
    """ Convert any Python object into an robject.
    :param o: object
    :rtype: :class:`rpy2.robjects.RObject (and subclasses)`
    """
    res = default_py2ri(o)
    return default_ri2py(res)

conversion.py2ro = default_py2ro




class Environment(RObjectMixin, rinterface.SexpEnvironment):
    """ An R environement. """
    
    def __init__(self, o=None):
        if o is None:
            o = rinterface.baseenv["new.env"](hash=rinterface.SexpVector([True, ], rinterface.LGLSXP))
        super(Environment, self).__init__(o)

    def __getitem__(self, item):
        res = super(Environment, self).__getitem__(item)
        res = conversion.ri2py(res)
        res.__rname__ = item
        return res

    def __setitem__(self, item, value):
        robj = conversion.py2ro(value)
        super(Environment, self).__setitem__(item, robj)

    def get(self, item, wantfun = False):
        """ Get a object from its R name/symol
        :param item: string (name/symbol)
        :rtype: object (as returned by :func:`conversion.ri2py`)
        """
        res = super(Environment, self).get(item, wantfun = wantfun)
        res = conversion.ri2py(res)
        res.__rname__ = item
        return res




class Formula(RObjectMixin, rinterface.Sexp):

    def __init__(self, formula, environment = rinterface.globalenv):
        if isinstance(formula, str):
            inpackage = rinterface.baseenv["::"]
            asformula = inpackage(rinterface.StrSexpVector(['stats', ]), 
                                  rinterface.StrSexpVector(['as.formula', ]))
            formula = rinterface.SexpVector(rinterface.StrSexpVector([formula, ]))
            robj = asformula(formula,
                             env = environment)
        else:
            robj = formula
        super(Formula, self).__init__(robj)
        
    def getenvironment(self):
        """ Get the environment in which the formula is finding its symbols."""
        res = self.do_slot(".Environment")
        res = conversion.ri2py(res)
        return res

    def setenvironment(self, val):
        """ Set the environment in which a formula will find its symbols."""
        if not isinstance(val, rinterface.SexpEnvironment):
            raise ValueError("The environment must be an instance of" +
                             " rpy2.rinterface.Sexp.environment")
        self.do_slot_assign(".Environment", val)

    environment = property(getenvironment, setenvironment,
                           "R environment in which the formula will look for" +
                           " its variables.")

    
class R(object):
    _instance = None

    def __init__(self):
        if R._instance is None:
            rinterface.initr()
            R._instance = self
        else:
            pass
            #raise(RuntimeError("Only one instance of R can be created"))
        
    def __getattribute__(self, attr):
        try:
            return super(R, self).__getattribute__(attr)
        except AttributeError, ae:
            orig_ae = ae

        try:
            return self[attr]
        except LookupError, le:
            raise orig_ae

    def __getitem__(self, item):
        res = rinterface.globalenv.get(item)
        res = conversion.ri2py(res)
        res.__rname__ = item
        return res

    #FIXME: check that this is properly working
    def __cleanup__(self):
        rinterface.endEmbeddedR()
        del(self)

    def __str__(self):
        s = super(R, self).__str__()
        s += os.linesep
        version = self["version"]
        tmp = [n+': '+val[0] for n, val in itertools.izip(version.names, version)]
        s += str.join(os.linesep, tmp)
        return s

    def __call__(self, string):
        p = self.parse(text=string)
        res = self.eval(p)
        return res

r = R()

globalenv = conversion.ri2py(rinterface.globalenv)
baseenv = conversion.ri2py(rinterface.baseenv)
emptyenv = conversion.ri2py(rinterface.emptyenv)
