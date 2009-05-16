from rpy2.robjects.robject import RObjectMixin, RObject
import rpy2.rinterface as rinterface
#import rpy2.robjects.conversion as conversion
import conversion

import rpy2.rlike.container as rlc

globalenv_ri = rinterface.globalEnv
baseenv_ri = rinterface.baseNameSpaceEnv

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
        res = globalenv_ri.get("+")(self._parent, conversion.py2ri(x))
        return res

    def __sub__(self, x):
        res = globalenv_ri.get("-")(self._parent, conversion.py2ri(x))
        return res

    def __mul__(self, x):
        res = globalenv_ri.get("*")(self._parent, conversion.py2ri(x))
        return res

    def __pow__(self, x):
        res = globalenv_ri.get("^")(self._parent, conversion.py2ri(x))
        return res

    def __div__(self, x):
        res = globalenv_ri.get("/")(self._parent, conversion.py2ri(x))
        return res

    def __divmod__(self, x):
        res = globalenv_ri.get("%%")(self._parent, conversion.py2ri(x))
        return res

    def __or__(self, x):
        res = globalenv_ri.get("|")(self._parent, conversion.py2ri(x))
        return res

    def __and__(self, x):
        res = globalenv_ri.get("&")(self._parent, conversion.py2ri(x))
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
        
        res = conversion.py2ri(globalenv_ri.get("["))(*([self, ] + [x for x in args]), **kwargs)
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
        res = conversion.py2ri(globalenv_ri.get("[<-")).rcall(args.items(), globalenv_ri)
        #FIXME: check that the R class remains the same ?
        self.__sexp__ = res.__sexp__


    def __add__(self, x):
        res = baseenv_ri.get("c")(self, conversion.py2ri(x))
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
        res = baseenv_ri.get('names')(self)
        res = conversion.py2ro(res)
        return res

    def setnames(self, value):
        """ Set the element names
        (like the R function 'names<-' does it)."""

        res = conversion.ri2py(globalenv_ri.get("names<-"))(self, value)
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
        if not baseenv_ri.get("is.array")(self)[0]:
            raise(TypeError("The object must be representing an R array"))

    def getdim(self):
        res = globalenv_ri.get("dim")(self)
        res = conversion.ri2py(res)
        return res

    def setdim(self, value):
        value = conversion.py2ro(value)
        res = globalenv_ri.get("dim<-")(self, value)
            #FIXME: not properly done
        raise(Exception("Not yet implemented"))

    dim = property(getdim, setdim, 
                   "Dimension of the array.")

    def getnames(self):
        """ Return a list of name vectors
        (like the R function 'dimnames' does it)."""

        res = globalenv_ri.get("dimnames")(self)
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
    _dataframe_name = rinterface.StrSexpVector(('data.frame',))
    
    def __init__(self, tlist):
        """ Create a new data frame.

        :param tlist: rpy2.rlike.container.TaggedList or rpy2.rinterface.SexpVector (and of class 'data.frame' for R)
        """
        if isinstance(tlist, rlc.TaggedList):
            df = baseenv_ri.get("data.frame").rcall(tlist.items(), globalenv_ri)
            super(RDataFrame, self).__init__(df)
        elif isinstance(tlist, rinterface.SexpVector):
            if tlist.typeof != rinterface.VECSXP:
                raise ValueError("tlist should of typeof VECSXP")
            if not globalenv_ri.get('inherits')(tlist, self._dataframe_name)[0]:
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
        return baseenv_ri.get("nrow")(self)[0]

    def ncol(self):
        """ Number of columns.
        :rtype: integer """
        return baseenv_ri.get("ncol")(self)[0]
    
    def rownames(self):
        """ Row names
        
        :rtype: SexpVector
        """
        res = baseenv_ri.get("rownames")(self)
        return conversion.ri2py(res)

    def colnames(self):
        """ Column names

        :rtype: SexpVector
        """
        res = baseenv_ri("colnames")(self)
        return conversion.ri2py(res)


class RFunction(RObjectMixin, rinterface.SexpClosure):
    """ An R function.
    
    """

    __formals = baseenv_ri.get('formals')
    __local = baseenv_ri.get('local')
    __call = baseenv_ri.get('call')
    __assymbol = baseenv_ri.get('as.symbol')
    __newenv = baseenv_ri.get('new.env')

    _local_env = None

    def __init__(self, *args, **kwargs):
        super(RFunction, self).__init__(*args, **kwargs)
        self._local_env = self.__newenv(hash=rinterface.BoolSexpVector((True, )))

    def __call__(self, *args, **kwargs):
        new_args = [conversion.py2ri(a) for a in args]
	new_kwargs = {}
        for k, v in kwargs.iteritems():
            new_kwargs[k] = conversion.py2ri(v)
        res = super(RFunction, self).__call__(*new_args, **new_kwargs)
        res = conversion.ri2py(res)
        return res

    def formals(self):
        """ Return the signature of the underlying R function 
        (as the R function 'formals' would). """
        res = self.__formals(self)
        res = conversion.ri2py(res)
        return res
