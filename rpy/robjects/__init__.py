"""
R objects as Python objects.

The module is structured around the singleton r of class R,
that represents an embedded R.

"""

import os, sys
import array
import rpy2.rinterface as rinterface

StrSexpVector = rinterface.StrSexpVector
IntSexpVector = rinterface.IntSexpVector
FloatSexpVector = rinterface.FloatSexpVector


#FIXME: close everything when leaving (check RPy for that).

def default_ri2py(o):
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

#FIXME: clean and nice mechanism to allow user-specified mapping function
#FIXME: better names for the functions
ri2py = default_ri2py


def default_py2ri(o):
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
    elif isinstance(o, int):
        res = rinterface.SexpVector([o, ], rinterface.INTSXP)
    elif isinstance(o, float):
        res = rinterface.SexpVector([o, ], rinterface.REALSXP)
    elif isinstance(o, str):
        res = rinterface.SexpVector([o, ], rinterface.STRSXP)
    elif isinstance(o, list):
        res = r.list(*[ri2py(py2ri(x)) for x in o])
    else:
        raise(ValueError("Nothing can be done for this type at the moment."))
    return res

py2ri = default_py2ri


def default_py2ro(o):
    res = default_py2ri(o)
    return default_ri2py(res)

py2ro = default_py2ro


def repr_robject(o):
    s = r.deparse(o)
    s = str.join(os.linesep, s)
    return s


class RObjectMixin(object):
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
            baseNameSpaceEnv["unlink"](tfile)
        else:
            r.close(tmp)
        s = str.join(os.linesep, s)
        return s

    def __repr__(self):
        return repr_robject(self)

    def rclass(self):
        """ Return the name of the R class for the object. """
        return baseNameSpaceEnv["class"](self)


class RObject(RObjectMixin, rinterface.Sexp):
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
            o = py2ri(o)
        super(RVector, self).__init__(o)
        self.r = RVectorDelegator(self)
            

    def subset(self, *args, **kwargs):
        """ Subset the "R-way.", using R's "[" function. 
           In a nutshell, R indexing differs from Python's with
           - indexing can be done with integers or strings (that are 'names')
           - an index equal to TRUE will mean everything selected (because of the recycling rule)
           - integer indexing starts at one
           - negative integer indexing means exclusion of the given integers
           - an index is itself a vector of elements to select
        """
        
        #for a in args:
        #    if not isinstance(a, Rvector):
        #        raise(TypeError("Subset only take R vectors"))
        args = [py2ro(x) for x in args]
        for k, v in kwargs.itervalues():
            args[k] = py2ro(v)
        
        res = r["["](*([self, ] + [x for x in args]), **kwargs)
        return res

    def assign(self, *args):
        #FIXME: value must be the last argument, but this can be
        # challenging in since python kwargs do not enforce any order
        #(an ordered dictionary class will therefore be implemented)
        args = [py2ro(x) for x in args]
        res = r["[<-"](*([self, ] + [x for x in args]))

        return res

    def __add__(self, x):
        res = r.get("c")(self, x)
        return res

    def __getitem__(self, i):
        res = super(RVector, self).__getitem__(i)
        if isinstance(res, rinterface.Sexp):
            res = ri2py(res)
        return res

    def __setitem__(self, i, value):
        value = py2ri(value)
        res = super(RVector, self).__setitem__(i, value)

    def getnames(self):
        res = r.names(self)
        return res

    def setnames(self, value):
        """ Return a vector of names
        (like the R function 'names' does it)."""

        res = r["names<-"](self, value)
        return res

class RArray(RVector):
    """ An R array """
    def __init__(self, o):
        super(RArray, self).__init__(o)
        #import pdb; pdb.set_trace()
        if not r["is.array"](self)[0]:
            raise(TypeError("The object must be representing an R array"))

    def __getattr__(self, name):
        if name == 'dim':
            res = r.dim(self)
            res = ri2py(res)
            return res

    def __setattr__(self, name, value):
        if name == 'dim':
            value = py2ro(value)
            res = r["dim<-"](self, value)
            #FIXME: not properly done
            raise(Exception("Not yet implemented"))

    def getnames(self):
        """ Return a list of name vectors
        (like the R function 'dimnames' does it)."""

        res = r.dimnames(self)
        return res
        


class RMatrix(RArray):
    """ An R matrix """

    def nrow(self):
        """ Number of rows """
        return self.dim[0]

    def ncol(self):
        """ Number of columns """
        return self.dim[1]

class RDataFrame(RVector):
    def __init__(self, *args, **kwargs):

        if len(args) > 1:
            raise(ValueError("Only one unnamed parameter is allowed."))

        if len(args) == 1:
            if len(kwargs) != 0:
                raise(ValueError("No named parameters allowed when there is an unnamed parameter."))
            else:
                super(RDataFrame, self).__init__(args[0])
        else:
            if len(kwargs) == 0:
                raise(ValueError("Initialization parameters needed."))
            df = baseNameSpaceEnv["data.frame"](**kwargs)
            super(RDataFrame, self).__init__(df)

        #import pdb; pdb.set_trace()
        if not baseNameSpaceEnv["is.data.frame"](self)[0]:
            raise(TypeError("The object must be representing an R data.frame"))
    
    def nrow(self):
        """ Number of rows """
        return baseNameSpaceEnv["nrow"](self)[0]

    def ncol(self):
        """ Number of columns """
        return baseNameSpaceEnv["ncol"](self)[0]
    
    def rownames(self):
        return baseNameSpaceEnv["colnames"](self)[0]

    def colnames(self):
        return baseNameSpaceEnv["colnames"](self)[0]



class RFunction(RObjectMixin, rinterface.SexpClosure):
    """ An R function (aka "closure").
    
    """

    def __call__(self, *args, **kwargs):
        new_args = [py2ri(a) for a in args]
	new_kwargs = {}
        for k, v in kwargs.iteritems():
            new_kwargs[k] = py2ri(v)
        res = super(RFunction, self).__call__(*new_args, **new_kwargs)
        res = ri2py(res)
        return res


class REnvironment(RObjectMixin, rinterface.SexpEnvironment):
    """ An R environement. """
    
    def __init__(self, o=None):
        if o is None:
            o = rinterface.baseNameSpaceEnv["new.env"](hash=rinterface.SexpVector([True, ], rinterface.LGLSXP))
        super(REnvironment, self).__init__(o)

    def __getitem__(self, item):
        res = super(REnvironment, self).__getitem__(item)
        res = ri2py(res)
        return res

    def __setitem__(self, item, value):
        robj = py2ro(value)
        super(REnvironment, self).__setitem__(item, robj)

    def get(self, item):
        res = super(REnvironment, self).get(item)
        res = ri2py(res)
        return res


class RS4(RObjectMixin, rinterface.SexpS4):

    def __getattr__(self, attr):
        res = self.do_slot(attr)
        res = ri2py(res)
        return res


class RFormula(RObjectMixin, rinterface.Sexp):

    def __init__(self, formula, environment = rinterface.globalEnv):
        inpackage = rinterface.baseNameSpaceEnv["::"]
        asformula = inpackage(StrSexpVector(['stats', ]), 
                              StrSexpVector(['as.formula', ]))
        robj = asformula(rinterface.SexpVector(StrSexpVector([formula, ])),
                         env = environment)
        super(RFormula, self).__init__(robj)
        
    def getenvironment(self):
        """ Return the R environment in which the formula will look for
        its variables. """
        res = self.do_slot(".Environment")
        res = ri2py(res)
        return res

    

    
class R(object):
    _instance = None

    def __init__(self):
        if R._instance is None:
            rinterface.initEmbeddedR()
            R._instance = self
        else:
            raise(ValueError("Only one instance of R can be created"))
        
    def __getattribute__(self, attr):
        return self[attr]

    def __getitem__(self, item):
        res = rinterface.globalEnv.get(item)
	res = ri2py(res)
        return res

    #FIXME: check that this is properly working
    def __cleanup__(self):
        rinterface.endEmbeddedR()
        del(self)

    def __str__(self):
        s = super(R, self).__str__()
        s += str(self["version"])
        return s

    def __call__(self, string):
        p = self.parse(text=string)
        res = self.eval(p)
        return res

r = R()

globalEnv = ri2py(rinterface.globalEnv)
baseNameSpaceEnv = ri2py(rinterface.baseNameSpaceEnv)

