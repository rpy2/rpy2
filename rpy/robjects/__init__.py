"""
R objects as Python objects.

The module is structured around the singleton r of class R,
that represents an embedded R.

"""

import os
import array
import rpy2.rinterface as rinterface


#FIXME: close everything when leaving (check RPy for that).

def defaultRobjects2PyMapper(o):
    if isinstance(o, rinterface.SexpVector):
        res = Rvector(o)
    elif isinstance(o, rinterface.SexpClosure):
        res = Rfunction(o)
    elif isinstance(o, rinterface.SexpEnvironment):
        res = Renvironment(o)
    elif isinstance(o, rinterface.SexpS4):
        res = RS4(o)
    else:
        res = Robject(o)
    return res

#FIXME: clean and nice mechanism to allow user-specified mapping function
#FIXME: better names for the functions
mapperR2Py = defaultRobjects2PyMapper

def defaultPy2Rinterface(o):
    if isinstance(o, Robject):
        return o._sexp
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
        res = r.list(*[defaultPy2RobjectsMapper(x) for x in o])
    else:
        raise(ValueError("Nothing can be done for this type at the moment."))
    return res

def defaultPy2RobjectsMapper(o):
    res = defaultPy2Rinterface(o)
    return mapperR2Py(res)

mapperPy2R = defaultPy2RobjectsMapper


def repr_robject(o):
    s = r.deparse(o)
    s = str.join(os.linesep, s)
    return s


class Robject(object):
    name = None
    _sexp = None

    def __init__(self, sexp, copy=True):
        self._sexp = rinterface.Sexp(sexp, copy=copy)

    def __str__(self):
        tmp = baseNameSpaceEnv["fifo"]("")
        baseNameSpaceEnv["sink"](tmp)
        r.show(self)
        baseNameSpaceEnv["sink"]()
        s = baseNameSpaceEnv["readLines"](tmp)
        r.close(tmp)
        s = str.join(os.linesep, s)
        return s

    def __repr__(self):
        return repr_robject(self)

    def __setattr__(self, name, value):
        if name == '_sexp':
            if not isinstance(value, rinterface.Sexp):
                raise ValueError("_attr must contain an object " +\
                                     "that inherits from rinterface.Sexp" +\
                                     "(not from %s)" %type(value))
        super(Robject, self).__setattr__(name, value)

    def getSexp(self):
        return self._sexp

    def typeof(self):
        return self._sexp.typeof()

    def do_slot(self, name):
        return self._sexp.do_slot(name)

    def rclass(self):
        return baseNameSpaceEnv["class"](self.getSexp())

class Rvector(Robject):
    """ R vector-like object. Items in those instances can
       be accessed with the method "__getitem__" ("[" operator),
       or with the method "subset"."""

    def __init__(self, o):
        if not isinstance(o, rinterface.SexpVector):
            o = mapperPy2R(o)
            o = o.getSexp()
        self._sexp = o
            

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
        args = [mapperPy2R(x) for x in args]
        for k, v in kwargs.itervalues():
            args[k] = mapperPy2R(v)
        
        res = r["["](*([self, ] + [x for x in args]), **kwargs)
        return res

    def __getitem__(self, i):
        res = self._sexp[i]
        if isinstance(res, rinterface.Sexp):
            res = mapperR2Py(res)
        return res

    def __repr__(self):
        return repr_robject(self)
        
    def __add__(self, x):
        res = r.get("+")(self.getSexp(), x)
        return res

    def __sub__(self, x):
        res = r.get("-")(self.getSexp(), x)
        return res

    def __mul__(self, x):
        res = r.get("*")(self.getSexp(), x)
        return res

    def __div__(self, x):
        res = r.get("/")(self.getSexp(), x)
        return res

    def __divmod__(self, x):
        res = r.get("%%")(self.getSexp(), x)
        return res

    def __or__(self, x):
        res = r.get("|")(self.getSexp(), x)
        return res

    def __and__(self, x):
        res = r.get("&")(self.getSexp(), x)
        return res

    def __len__(self):
        return len(self.getSexp())

    def getNames(self):
        res = r.names(self.getSexp())
        return res

class RArray(Rvector):
    """ An R array """
    def __init__(self, o):
        super(RArray, self).__init__(o)
        if not r["is.array"](self.getSexp())[0]:
            raise(TypeError("The object must be reflecting an R array"))

    def __getattr__(self, name):
        if name == 'dim':
            res = r.dim(self.getSexp())
            res = mapperR2Py(res)
            return res

    def __setattr__(self, name, value):
        if name == 'dim':
            value = mapperPy2R
            res = r["dim<-"](value)
        

class RMatrix(RArray):
    """ An R matrix """

    def nrow(self):
        """ Number of rows """
        return self.dim[0]

    def ncol(self):
        """ Number of columns """
        return self.dim[1]

class DataFrame(Rvector):
    #FIXME: not implemented
    def __init__(self, o):
        if not isinstance(o, rinterface.SexpVector):
            o = mapperPy2R(o)
            o = o.getSexp()
        self._sexp = o



class Rfunction(Robject):
    """ An R function (aka "closure").
    
    """
    def __init__(self, sexp):
        # arbirtary python functions for v-2.1
        self._sexp = rinterface.SexpClosure(sexp)

    def __call__(self, *args, **kwargs):
        new_args = [mapperPy2R(a).getSexp() for a in args]
	new_kwargs = {}
        for k, v in kwargs.iteritems():
            new_kwargs[k] = mapperPy2R(v).getSexp()
        res = self.getSexp()(*new_args, **new_kwargs)
        res = mapperR2Py(res)
        return res

    #def getSexp(self):
    #    return super(rinterface.SexpClosure, self).__init__(self)

class Renvironment(Robject):
    """ An R environement. """
    
    def __init__(self, o=None):
        if o is None:
            o = rinterface.baseNameSpaceEnv["new.env"](hash=rinterface.SexpVector([True, ], rinterface.LGLSXP))
        self._sexp = rinterface.SexpEnvironment(o)

    def __getitem__(self, item):
        res = self._sexp[item]
        res = mapperR2Py(res)
        return res

    def __setitem__(self, item, value):
        robj = mapperPy2R(value)
        self._sexp[item] = robj.getSexp()

    def __iter__(self):
        return iter(self._sexp)

    def get(self, item):
        res = self.getSexp().get(item)
        res = mapperR2Py(res)
        return res

class RS4(Robject):
    def __init__(self, o):
        if (isinstance(o, rinterface.SexpS4)):
            self._sexp = o
        else:
            raise(ValueError("Cannot instantiate"))

    def __getattr__(self, attr):
        res = r.get("@")(self, attr)
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
	res = mapperR2Py(res)
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

globalEnv = mapperR2Py(rinterface.globalEnv)
baseNameSpaceEnv = mapperR2Py(rinterface.baseNameSpaceEnv)

