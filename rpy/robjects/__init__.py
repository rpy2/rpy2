"""
R objects as Python objects.

The module is structured around the singleton r of class R,
that represents an embedded R.

"""

import os, sys
import array
import itertools
import rpy2.rinterface as rinterface
import rpy2.rlike.container as rlc
import rpy2.robjects.conversion

#FIXME: close everything when leaving (check RPy for that).


def default_ri2py(o):
    """ Convert :class:`rpy2.rinterface.Sexp` to higher-level objects,
    without copying the R objects.

    :param o: object
    :rtype: :class:`rpy2.robjects.RObject (and subclasses)`
    """

    res = None
    if isinstance(o, RObject):
        res = o
    elif isinstance(o, rinterface.SexpVector):
        try:
           cl = o.do_slot("class")[0]
           if cl == 'data.frame':
               res = RDataFrame(o)
        except LookupError, le:
            pass
        if res is None:
            try:
                dim = o.do_slot("dim")
                res = RArray(o)
            except LookupError, le:
                res = RVector(o)
    elif isinstance(o, rinterface.SexpClosure):
        res = RFunction(o)
    elif isinstance(o, rinterface.SexpEnvironment):
        res = REnvironment(o)
    elif isinstance(o, rinterface.SexpS4):
        res = RS4(o)
    elif rinterface.baseNameSpaceEnv['class'](o)[0] == 'formula':
        res = RFormula(o)
    else:
        res = RObject(o)
    return res

conversion.ri2py = default_ri2py


def default_py2ri(o):
    """ Convert arbitrary Python object to :class:`rpy2.rinterface.Sexp` to objects,
    creating an R object with the content of the Python object in the process
    (wichi means data copying).

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


def repr_robject(o, linesep=os.linesep):
    s = r.deparse(o)
    s = str.join(linesep, s)
    return s


class RObjectMixin(object):
    """ Class to provide methods common to all RObject instances """
    name = None

    def __str__(self):
        if sys.platform == 'win32':
            tfile = baseNameSpaceEnv["tempfile"]()
            tmp = baseNameSpaceEnv["file"](tfile, open="w")
        else:
            tmp = baseNameSpaceEnv["fifo"]("")
        baseNameSpaceEnv["sink"](tmp)
        r.show(self)
        baseNameSpaceEnv["sink"]()
        if sys.platform == 'win32':
            baseNameSpaceEnv["close"](tmp)
            tmp = baseNameSpaceEnv["file"](tfile, open="r")
        s = baseNameSpaceEnv["readLines"](tmp)
        if sys.platform == 'win32':
            baseNameSpaceEnv["close"](tmp)
            baseNameSpaceEnv["unlink"](tfile)
        else:
            r.close(tmp)
        s = str.join(os.linesep, s)
        return s

    def r_repr(self):
        """ R string representation for an object.
        This string representation can be used directed
        in R code.
        """
        return repr_robject(self, linesep='\n')

    def getrclass(self):
        """ Return the name of the R class for the object. """
        return baseNameSpaceEnv["class"](self)

    rclass = property(getrclass)

class RObject(RObjectMixin, rinterface.Sexp):
    """ Base class for all R objects. """
    def __setattr__(self, name, value):
        if name == '_sexp':
            if not isinstance(value, rinterface.Sexp):
                raise ValueError("_attr must contain an object " +\
                                     "that inherits from rinterface.Sexp" +\
                                     "(not from %s)" %type(value))
        super(RObject, self).__setattr__(name, value)

class RVectorDelegator(object):
    """
    Delegate operations such as __getitem__, __add__, etc..
    to an R call of the corresponding function on its parent
    attribute.
    This permits a convenient coexistence between
    operators on Python sequence object with their R conterparts.
    """

    def __init__(self, parent):
        """ The parent in expected to inherit from RVector. """
        self._parent = parent

    def __getitem__(self, *args, **kwargs):
        res = self._parent.subset(*args, **kwargs)
        return res

    def __add__(self, x):
        res = r.get("+")(self._parent, x)
        return res

    def __sub__(self, x):
        res = r.get("-")(self._parent, x)
        return res

    def __mul__(self, x):
        res = r.get("*")(self._parent, x)
        return res

    def __pow__(self, x):
        res = r.get("^")(self._parent, x)
        return res

    def __div__(self, x):
        res = r.get("/")(self._parent, x)
        return res

    def __divmod__(self, x):
        res = r.get("%%")(self._parent, x)
        return res

    def __or__(self, x):
        res = r.get("|")(self._parent, x)
        return res

    def __and__(self, x):
        res = r.get("&")(self._parent, x)
        return res

class RVector(RObjectMixin, rinterface.SexpVector):
    """ R vector-like object. Items in those instances can
       be accessed with the method "__getitem__" ("[" operator),
       or with the method "subset"."""

    def __init__(self, o):
        if not isinstance(o, rinterface.SexpVector):
            o = conversion.py2ri(o)
        super(RVector, self).__init__(o)
        self.r = RVectorDelegator(self)
            

    def subset(self, *args, **kwargs):
        """ Subset the "R-way.", using R's "[" function. 
           In a nutshell, R indexing differs from Python's on:

           - indexing can be done with integers or strings (that are 'names')

           - an index equal to TRUE will mean everything selected (because of the recycling rule)

           - integer indexing starts at one

           - negative integer indexing means exclusion of the given integers

           - an index is itself a vector of elements to select
        """
        
        args = [conversion.py2ro(x) for x in args]
        for k, v in kwargs.itervalues():
            args[k] = conversion.py2ro(v)
        
        res = r["["](*([self, ] + [x for x in args]), **kwargs)
        return res

    def assign(self, index, value):
        """ Assign a given value to a given index position in the vector """
        if not (isinstance(index, rlc.TaggedList) | \
                    isinstance(index, rlc.ArgsDict)):
            args = rlc.TaggedList([conversion.py2ro(index), ])
        else:
            for i in xrange(len(index)):
                index[i] = conversion.py2ro(index[i])
            args = index
        args.append(conversion.py2ro(value))
        args.insert(0, self)
        res = r["[<-"].rcall(args.items())
        res = conversion.ri2py(res)
        return res

    def __add__(self, x):
        res = r.get("c")(self, x)
        return res

    def __getitem__(self, i):
        res = super(RVector, self).__getitem__(i)
        if isinstance(res, rinterface.Sexp):
            res = conversion.ri2py(res)
        return res

    def __setitem__(self, i, value):
        value = conversion.py2ri(value)
        res = super(RVector, self).__setitem__(i, value)

    def getnames(self):
        """ Get the element names, calling the R function names(). """
        res = r.names(self)
        return res

    def setnames(self, value):
        """ Set the element names
        (like the R function 'names<-' does it)."""

        res = r["names<-"](self, value)
        return res

    names = property(getnames, setnames, 
                     "Names for the items in the vector.")


class StrVector(RVector):
    """ Vector of string elements """
    def __init__(self, obj):
        obj = rinterface.StrSexpVector(obj)
        super(StrVector, self).__init__(obj)

class IntVector(RVector):
    """ Vector of integer elements """
    def __init__(self, obj):
        obj = rinterface.IntSexpVector(obj)
        super(IntVector, self).__init__(obj)

class BoolVector(RVector):
    """ Vector of boolean (logical) elements """
    def __init__(self, obj):
        obj = rinterface.BoolSexpVector(obj)
        super(BoolVector, self).__init__(obj)

class FloatVector(RVector):
    """ Vector of float (double) elements """
    def __init__(self, obj):
        obj = rinterface.FloatSexpVector(obj)
        super(FloatVector, self).__init__(obj)


class RArray(RVector):
    """ An R array """
    def __init__(self, o):
        super(RArray, self).__init__(o)
        #import pdb; pdb.set_trace()
        if not r["is.array"](self)[0]:
            raise(TypeError("The object must be representing an R array"))

    def getdim(self):
        res = r.dim(self)
        res = conversion.ri2py(res)
        return res

    def setdim(self, value):
        value = conversion.py2ro(value)
        res = r["dim<-"](self, value)
            #FIXME: not properly done
        raise(Exception("Not yet implemented"))

    dim = property(getdim, setdim, 
                   "Dimension of the array.")

    def getnames(self):
        """ Return a list of name vectors
        (like the R function 'dimnames' does it)."""

        res = r.dimnames(self)
        return res
        
    names = property(getnames)


class RMatrix(RArray):
    """ An R matrix """

    def nrow(self):
        """ Number of rows.
        :rtype: integer """
        return self.dim[0]

    def ncol(self):
        """ Number of columns.
        :rtype: integer """
        return self.dim[1]

class RDataFrame(RVector):
    """ R 'data.frame'.
    """

    def __init__(self, tlist):
        """ Create a new data frame.

        :param tlist: rpy2.rlike.container.TaggedList or rpy2.rinterface.SexpVector (and of class 'data.frame' for R)
        """
        if isinstance(tlist, rlc.TaggedList):
            df = baseNameSpaceEnv["data.frame"].rcall(tlist.items())
            super(RDataFrame, self).__init__(df)
        elif isinstance(tlist, rinterface.SexpVector):
            if tlist.typeof != rinterface.VECSXP:
                raise ValueError("tlist should of typeof VECSXP")
            if not r['inherits'](tlist, 'data.frame')[0]:
                raise ValueError('tlist should of R class "data.frame"')
            super(RDataFrame, self).__init__(tlist)
        else:
            raise ValueError("tlist can be either"+
                             " an instance of rpy2.rlike.container.TaggedList" +
                             " or an instance of rpy2.rinterface.SexpVector" +
                             " of type VECSXP.")
    
    def nrow(self):
        """ Number of rows. 
        :rtype: integer """
        return baseNameSpaceEnv["nrow"](self)[0]

    def ncol(self):
        """ Number of columns.
        :rtype: integer """
        return baseNameSpaceEnv["ncol"](self)[0]
    
    def rownames(self):
        """ Row names
        
        :rtype: SexpVector
        """
        res = baseNameSpaceEnv["rownames"](self)
        return conversion.ri2py(res)

    def colnames(self):
        """ Column names

        :rtype: SexpVector
        """
        res = baseNameSpaceEnv["colnames"](self)
        return conversion.ri2py(res)


class RFunction(RObjectMixin, rinterface.SexpClosure):
    """ An R function.
    
    """

    def __call__(self, *args, **kwargs):
        new_args = [conversion.py2ri(a) for a in args]
	new_kwargs = {}
        for k, v in kwargs.iteritems():
            new_kwargs[k] = conversion.py2ri(v)
        res = super(RFunction, self).__call__(*new_args, **new_kwargs)
        res = conversion.ri2py(res)
        return res


class REnvironment(RObjectMixin, rinterface.SexpEnvironment):
    """ An R environement. """
    
    def __init__(self, o=None):
        if o is None:
            o = rinterface.baseNameSpaceEnv["new.env"](hash=rinterface.SexpVector([True, ], rinterface.LGLSXP))
        super(REnvironment, self).__init__(o)

    def __getitem__(self, item):
        res = super(REnvironment, self).__getitem__(item)
        res = conversion.ri2py(res)
        return res

    def __setitem__(self, item, value):
        robj = conversion.py2ro(value)
        super(REnvironment, self).__setitem__(item, robj)

    def get(self, item, wantFun = False):
        """ Get a object from its R name/symol
        :param item: string (name/symbol)
        :param wantFun: boolean (fetch preferably a function or not)
        :rtype: object (as returned by :func:`conversion.ri2py`)
        """
        res = super(REnvironment, self).get(item, wantFun = wantFun)
        res = conversion.ri2py(res)
        return res


class RS4(RObjectMixin, rinterface.SexpS4):

    def __getattr__(self, attr):
        res = self.do_slot(attr)
        res = conversion.ri2py(res)
        return res


class RFormula(RObjectMixin, rinterface.Sexp):

    def __init__(self, formula, environment = rinterface.globalEnv):
        inpackage = rinterface.baseNameSpaceEnv["::"]
        asformula = inpackage(rinterface.StrSexpVector(['stats', ]), 
                              rinterface.StrSexpVector(['as.formula', ]))
        formula = rinterface.SexpVector(rinterface.StrSexpVector([formula, ]))
        robj = asformula(formula,
                         env = environment)
        super(RFormula, self).__init__(robj)
        
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
        res = rinterface.globalEnv.get(item)
            
	res = conversion.ri2py(res)
        return res

    #FIXME: check that this is properly working
    def __cleanup__(self):
        rinterface.endEmbeddedR()
        del(self)

    def __str__(self):
        s = super(R, self).__str__()
        s += os.linesep
        version = self["version"]
        tmp = [n+': '+val[0] for n, val in itertools.izip(version.getnames(), version)]
        s += str.join(os.linesep, tmp)
        return s

    def __call__(self, string):
        p = self.parse(text=string)
        res = self.eval(p)
        return res

r = R()

globalEnv = conversion.ri2py(rinterface.globalEnv)
baseNameSpaceEnv = conversion.ri2py(rinterface.baseNameSpaceEnv)
emptyEnv = conversion.ri2py(rinterface.emptyEnv)
