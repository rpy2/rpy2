from rpy2.robjects.robject import RObjectMixin, RObject
import rpy2.rinterface as rinterface
#import rpy2.robjects.conversion as conversion
import conversion

import rpy2.rlike.container as rlc

import copy, os, itertools

globalenv_ri = rinterface.globalenv
baseenv_ri = rinterface.baseenv
utils_ri = rinterface.baseenv['as.environment'](rinterface.StrSexpVector(("package:utils", )))

class ExtractDelegator(object):
    """ Delegate the R 'extraction' ("[") and 'replacement' ("[<-")
    of items in a vector
    or vector-like object. This can help making syntactic
    niceties possible."""
    
    _extractfunction = rinterface.baseenv['[']
    _replacefunction = rinterface.baseenv['[<-']

    def __init__(self, parent):
        self._parent = parent
        
    def __call__(self, *args, **kwargs):
        """ Subset the "R-way.", using R's "[" function. 
           In a nutshell, R indexing differs from Python indexing on:

           - indexing can be done with integers or strings (that are 'names')

           - an index equal to TRUE will mean everything selected
             (because of the recycling rule)

           - integer indexing starts at one

           - negative integer indexing means exclusion of the given integers

           - an index is itself a vector of elements to select
        """

        args = [conversion.py2ro(x) for x in args]
        kwargs = copy.copy(kwargs)
        for k, v in kwargs.itervalues():
            kwargs[k] = conversion.py2ro(v)
        fun = self._extractfunction
        args.insert(0, self._parent)
        res = fun(*args, **kwargs)
        res = conversion.py2ro(res)
        return res

    def __getitem__(self, item):
        fun = self._extractfunction
        args = rlc.TaggedList(item)
        for i, (k, v) in enumerate(args.iteritems()):
            args[i] = conversion.py2ro(v)
        args.insert(0, self._parent)
        res = fun.rcall(args.items(),
                        globalenv_ri)
        res = conversion.py2ro(res)
        return res

    def __setitem__(self, item, value):
        """ Assign a given value to a given index position in the vector """
        args = rlc.TaggedList.from_iteritems(item)
        for i, (k, v) in enumerate(args.iteritems()):
            args[i] = conversion.py2ro(v)
        args.append(conversion.py2ro(value), tag = None)
        args.insert(0, self._parent, tag = None)
        fun = self._replacefunction
        res = fun.rcall(tuple(args.iteritems()),
                        globalenv_ri)
        #FIXME: check refcount and copying
        self._parent.__sexp__ = res.__sexp__


class DoubleExtractDelegator(ExtractDelegator):
    """ Delegate the R 'extraction' ("[[") and "replacement" ("[[<-")
    of items in a vector
    or vector-like object. This can help making syntactic
    niceties possible."""
    _extractfunction = rinterface.baseenv['[[']
    _replacefunction = rinterface.baseenv['[[<-']


    
class VectorOperationsDelegator(object):
    """
    Delegate operations such as __getitem__, __add__, etc..
    to the corresponding R function.
    This permits a convenient coexistence between
    operators on Python sequence object with their R conterparts.
    """

    def __init__(self, parent):
        """ The parent in expected to inherit from Vector. """
        self._parent = parent

    def __add__(self, x):
        res = globalenv_ri.get("+")(self._parent, conversion.py2ri(x))
        return conversion.ri2py(res)

    def __sub__(self, x):
        res = globalenv_ri.get("-")(self._parent, conversion.py2ri(x))
        return conversion.ri2py(res)

    def __mul__(self, x):
        res = globalenv_ri.get("*")(self._parent, conversion.py2ri(x))
        return conversion.ri2py(res)

    def __pow__(self, x):
        res = globalenv_ri.get("^")(self._parent, conversion.py2ri(x))
        return conversion.ri2py(res)

    def __div__(self, x):
        res = globalenv_ri.get("/")(self._parent, conversion.py2ri(x))
        return conversion.ri2py(res)

    def __divmod__(self, x):
        res = globalenv_ri.get("%%")(self._parent, conversion.py2ri(x))
        return conversion.ri2py(res)

    def __or__(self, x):
        res = globalenv_ri.get("|")(self._parent, conversion.py2ri(x))
        return conversion.ri2py(res)

    def __and__(self, x):
        res = globalenv_ri.get("&")(self._parent, conversion.py2ri(x))
        return conversion.ri2py(res)

    # Comparisons

    def __lt__(self, x):
        res = globalenv_ri.get("<")(self._parent, conversion.py2ri(x))
        return conversion.ri2py(res)

    def __le__(self, x):
        res = globalenv_ri.get("<=")(self._parent, conversion.py2ri(x))
        return conversion.ri2py(res)

    def __eq__(self, x):
        res = globalenv_ri.get("==")(self._parent, conversion.py2ri(x))
        return conversion.ri2py(res)

    def __ne__(self, x):
        res = globalenv_ri.get("!=")(self._parent, conversion.py2ri(x))
        return conversion.ri2py(res)

    def __gt__(self, x):
        res = globalenv_ri.get(">")(self._parent, conversion.py2ri(x))
        return conversion.ri2py(res)

    def __ge__(self, x):
        res = globalenv_ri.get(">=")(self._parent, conversion.py2ri(x))
        return conversion.ri2py(res)
    
    # 
    def __neg__(self):
        res = globalenv_ri.get("-")(self._parent)
        return res


class Vector(RObjectMixin, rinterface.SexpVector):
    """ R vector-like object. Items can be accessed with:
    - the method "__getitem__" ("[" operator)
    - the delegators rx or rx2 """
    _sample = rinterface.baseenv['sample']

    def __init__(self, o):
        if not isinstance(o, rinterface.SexpVector):
            o = conversion.py2ri(o)
        super(Vector, self).__init__(o)
        self.ro = VectorOperationsDelegator(self)
        self.rx = ExtractDelegator(self)
        self.rx2 = DoubleExtractDelegator(self)

    def __add__(self, x):
        res = baseenv_ri.get("c")(self, conversion.py2ri(x))
        res = conversion.ri2py(res)
        return res

    def __getitem__(self, i):
        res = super(Vector, self).__getitem__(i)
        if isinstance(res, rinterface.Sexp):
            res = conversion.ri2py(res)
        return res

    def __setitem__(self, i, value):
        value = conversion.py2ri(value)
        res = super(Vector, self).__setitem__(i, value)

    def _names_get(self):
        res = baseenv_ri.get('names')(self)
        res = conversion.ri2py(res)
        return res

    def _names_set(self, value):
        res = globalenv_ri.get("names<-")(self, conversion.py2ro(value))
        self.__sexp__ = res.__sexp__

    names = property(_names_get, _names_set, 
                     "Names for the items in the vector.")

    def iteritems(self):
        """ iterate over names and values """
        if self.names.rsame(rinterface.R_NilValue):
            it_names = itertools.cycle((None, ))
        else:
            it_names = iter(self.names)
        it_self  = iter(self)
        for v, k in zip(it_self, it_names):
            yield (k, v)

    def sample(self, n, replace = False, probabilities = None):
        """ Draw a sample of size n from the vector. 
        If 'replace' is True, the sampling is done with replacement.
        The optional argument 'probabilities' indicates sampling probabilities. """

        assert isinstance(n, int)
        assert isinstance(replace, bool)
        if probabilities is not None:
            probabilities = FloatVector(probabilities)
        res = self._sample(self, IntVector((n,)), 
                           replace = BoolVector((replace, )),
                           prob = probabilities)
        res = conversion.ri2py(res)
        return res

class StrVector(Vector):
    """ Vector of string elements """

    _factorconstructor = rinterface.baseenv['factor']

    def __init__(self, obj):
        obj = rinterface.StrSexpVector(obj)
        super(StrVector, self).__init__(obj)

    def factor(self):
        """ construct a factor vector from the vector of strings """
        res = self._factorconstructor(self)
        return conversion.ri2py(res)

class IntVector(Vector):
    """ Vector of integer elements """
    _tabulate = rinterface.baseenv['tabulate']

    def __init__(self, obj):
        obj = rinterface.IntSexpVector(obj)
        super(IntVector, self).__init__(obj)

    def tabulate(self, nbins = None):
        """ Count the number of times integer values are found """
        if nbins is None:
            nbins = max(1, max(self))
        res = self._tabulate(self)
        return conversion.ri2py(res)

class BoolVector(Vector):
    """ Vector of boolean (logical) elements """
    def __init__(self, obj):
        obj = rinterface.BoolSexpVector(obj)
        super(BoolVector, self).__init__(obj)

class ComplexVector(Vector):
    """ Vector of complex elements """
    def __init__(self, obj):
        obj = rinterface.ComplexSexpVector(obj)
        super(ComplexVector, self).__init__(obj)

class FloatVector(Vector):
    """ Vector of float (double) elements """
    def __init__(self, obj):
        obj = rinterface.FloatSexpVector(obj)
        super(FloatVector, self).__init__(obj)

class FactorVector(IntVector):
    """ Vector of 'factors' """

    _factor = baseenv_ri['factor']
    _levels = baseenv_ri['levels']
    _levels_set = baseenv_ri['levels<-']
    _nlevels = baseenv_ri['nlevels']
    _isordered = baseenv_ri['is.ordered']
    
    def __init__(self, obj, levels = rinterface.MissingArg,
                 labels = rinterface.MissingArg,
                 exclude = rinterface.MissingArg,
                 ordered = rinterface.MissingArg):
        if not isinstance(obj, rinterface.Sexp):
            obj = rinterface.StrSexpVector(obj)
        res = self._factor(obj,
                           levels = levels,
                           labels = labels,
                           exclude = exclude,
                           ordered = ordered)
        self.__sexp__ = res.__sexp__
        self.ro = VectorOperationsDelegator(self)
        self.rx = ExtractDelegator(self)
        self.rx2 = DoubleExtractDelegator(self)

    def __levels_get(self):
        res = self._levels(self)
        return conversion.ri2py(res)
    def __levels_set(self, value):
        res = self._levels_set(self, conversion.py2ro(value))
        self.__sexp__ = res.__sexp__

    levels = property(__levels_get, __levels_set)

    def __nlevels_get(self):
        res = self._nlevels(self)
        return res[0]
    nlevels = property(__nlevels_get, None, None, "number of levels ")

    def __isordered_get(self):
        res = self._isordered(self)
        return res[0]
    isordered = property(__isordered_get, None, None,
                         "are the levels in the factor ordered ?")

    
class Array(Vector):
    """ An R array """
    _dimnames_get = baseenv_ri['dimnames']
    _dimnames_set = baseenv_ri['dimnames<-']
    _dim_get = baseenv_ri['dim']
    _dim_set = baseenv_ri['dim<-']
    _isarray = baseenv_ri['is.array']

    def __init__(self, obj):
        super(Array, self).__init__(obj)
        #import pdb; pdb.set_trace()
        if not self._isarray(self)[0]:
            raise(TypeError("The object must be representing an R array"))

    def __dim_get(self):
        res = self._dim_get(self)
        res = conversion.ri2py(res)
        return res

    def __dim_set(self, value):
        value = conversion.py2ro(value)
        res = self._dim_set(self, value)
            #FIXME: not properly done
        raise(Exception("Not yet implemented"))

    dim = property(__dim_get, __dim_set, 
                   "Get or set the dimension of the array.")

    def __dimnames_get(self):
        """ Return a list of name vectors
        (like the R function 'dimnames' does it)."""

        res = self._dimnames_get(self)
        res = conversion.ri2py(res)
        return res

    def __dimnames_set(self, value):
        """ Return a list of name vectors
        (like the R function 'dimnames' does it)."""

        value = conversion.ri2py(value)
        res = self._dimnames_set(self, value)        
        self.__sexp__ = res.__sexp__
        
    names = property(__dimnames_get, __dimnames_set, None, 
                     "names associated with the dimension.")
    dimnames = names


class Matrix(Array):
    """ An R matrix """
    _transpose = baseenv_ri['t']
    _rownames = baseenv_ri['rownames']
    _colnames = baseenv_ri['colnames']
    _dot = baseenv_ri['%*%']
    _crossprod = baseenv_ri['crossprod']
    _tcrossprod = baseenv_ri['tcrossprod']
    _svd = baseenv_ri['svd']
    _eigen = baseenv_ri['eigen']

    def __nrow_get(self):
        """ Number of rows.
        :rtype: integer """
        return self.dim[0]
    nrow = property(__nrow_get, None, None, "Number of rows")

    def __ncol_get(self):
        """ Number of columns.
        :rtype: integer """
        return self.dim[1]
    ncol = property(__ncol_get, None, None, "Number of columns")

    def __rownames_get(self):
        """ Row names
        
        :rtype: SexpVector
        """
        res = self._rownames(self)
        return conversion.ri2py(res)
    rownames = property(__rownames_get, None, None, "Row names")

    def __colnames_get(self):
        """ Column names

        :rtype: SexpVector
        """
        res = self._colnames(self)
        return conversion.ri2py(res)
    colnames = property(__colnames_get, None, None, "Column names")
        
    def transpose(self):
        """ transpose the matrix """
        res = self._transpose(self)
        return conversion.ri2py(res)

    def crossprod(self, m):
        """ crossproduct X'.Y"""
        res = self._crossprod(self, conversion.ri2py(m))
        return conversion.ri2py(res)

    def tcrossprod(self, m):
        """ crossproduct X.Y'"""
        res = self._tcrossprod(self, m)
        return conversion.ri2py(res)

    def svd(self, nu = None, nv = None, linpack = False):
        """ SVD decomposition.
        If nu is None, it is given the default value min(tuple(self.dim)).
        If nv is None, it is given the default value min(tuple(self.dim)).
        """
        if nu is None:
            nu = min(tuple(self.dim))
        if nv is None:
            nv = min(tuple(self.dim))
        res = self._svd(self, nu = nu, nv = nv, LINPACK = False)
        return conversion.ri2py(res)

    def dot(self, m):
        """ Matrix multiplication """
        res = self._dot(self, m)
        return conversion.ri2py(res)

    def eigen(self):
        """ Eigen values """
        res = self._eigen(self)
        return conversion.ri2py(res)

class DataFrame(Vector):
    """ R 'data.frame'.
    """
    _dataframe_name = rinterface.StrSexpVector(('data.frame',))
    _read_csv  = utils_ri['read.csv']
    _write_table = utils_ri['write.table']
    _cbind     = rinterface.baseenv['cbind.data.frame']
    _rbind     = rinterface.baseenv['rbind.data.frame']
    
    def __init__(self, tlist):
        """ Create a new data frame.

        :param tlist: rpy2.rlike.container.TaggedList or rpy2.rinterface.SexpVector (and of class 'data.frame' for R)
        """
        if isinstance(tlist, rlc.TaggedList):
            df = baseenv_ri.get("data.frame").rcall(tlist.items(), globalenv_ri)
            super(DataFrame, self).__init__(df)
        elif isinstance(tlist, rinterface.SexpVector):
            if tlist.typeof != rinterface.VECSXP:
                raise ValueError("tlist should of typeof VECSXP")
            if not globalenv_ri.get('inherits')(tlist, self._dataframe_name)[0]:
                raise ValueError('tlist should of R class "data.frame"')
            super(DataFrame, self).__init__(tlist)
        elif isinstance(tlist, dict):
            kv = [(k, conversion.py2ri(v)) for k,v in tlist.iteritems()]
            kv = tuple(kv)
            df = baseenv_ri.get("data.frame").rcall(kv, globalenv_ri)
            super(DataFrame, self).__init__(df)
        else:
            raise ValueError("tlist can be either "+
                             "an instance of rpy2.rlike.container.TaggedList," +
                             " or an instance of rpy2.rinterface.SexpVector" +
                             " of type VECSXP, or a Python dict.")
    
    def _get_nrow(self):
        """ Number of rows. 
        :rtype: integer """
        return baseenv_ri["nrow"](self)[0]
    nrow = property(_get_nrow, None, None)

    def _get_ncol(self):
        """ Number of columns.
        :rtype: integer """
        return baseenv_ri["ncol"](self)[0]
    ncol = property(_get_ncol, None, None)
    
    def _get_rownames(self):
        res = baseenv_ri["rownames"](self)
        return conversion.ri2py(res)

    def _set_rownames(self, rownames):
        res = baseenv_ri["rownames<-"](self, conversion.py2ri(rownames))
        self.__sexp__ = res.__sexp__

    rownames = property(_get_rownames, _set_rownames, None, 
                        "Row names")

    def _get_colnames(self):
        res = baseenv_ri["colnames"](self)
        return conversion.ri2py(res)

    def _set_colnames(self, colnames):
        res = baseenv_ri["colnames<-"](self, conversion.py2ri(colnames))
        self.__sexp__ = res.__sexp__
        
    colnames = property(_get_colnames, _set_colnames, None)


    def cbind(self, *args, **kwargs):
        """ bind objects as supplementary columns """
        new_args   = [self, ] + [conversion.ri2py(x) for x in args]
        new_kwargs = dict([(k, conversion.ri2py(v)) for k,v in kwargs.iteritems()])
        res = self._cbind(*new_args, **new_kwargs)
        return conversion.ri2py(res)

    def rbind(self, *args, **kwargs):
        """ bind objects as supplementary rows """
        new_args   = [conversion.ri2py(x) for x in args]
        new_kwargs = dict([(k, conversion.ri2py(v)) for k,v in kwargs.iteritems()])
        res = self._rbind(self, *new_args, **new_kwargs)
        return conversion.ri2py(res)


    @staticmethod
    def from_csvfile(path, header = True, sep = ",",
                     quote = "\"", dec = ".", 
                     row_names = rinterface.MissingArg,
                     col_names = rinterface.MissingArg,
                     fill = True, comment_char = "",
                     as_is = False):
        """ Create an instance from data in a .csv file. """
        path = conversion.py2ro(path)
        header = conversion.py2ro(header)
        sep = conversion.py2ro(sep)
        quote = conversion.py2ro(quote)
        dec = conversion.py2ro(dec)
        row_names = conversion.py2ro(row_names)
        col_names = conversion.py2ro(col_names)
        fill = conversion.py2ro(fill)
        comment_char = conversion.py2ro(comment_char)
        as_is = conversion.py2ro(as_is)
        res = DataFrame._read_csv(path, 
                                  **{'header': header, 'sep': sep,
                                     'quote': quote, 'dec': dec,
                                     'row.names': row_names,
                                     'col.names': col_names,
                                     'fill': fill,
                                     'comment.char': comment_char,
                                     'as.is': as_is})
        res = conversion.ri2py(res)
        return res

    def to_csvfile(self, path, quote = True, sep = ",", eol = os.linesep, na = "NA", dec = ".", 
                   row_names = True, col_names = True, qmethod = "escape", append = False):
        """ Save the data into a .csv file. """
        path = conversion.py2ro(path)
        append = conversion.py2ro(append)
        sep = conversion.py2ro(sep)
        eol = conversion.py2ro(eol)
        na = conversion.py2ro(na)
        dec = conversion.py2ro(dec)
        row_names = conversion.py2ro(row_names)
        col_names = conversion.py2ro(col_names)
        qmethod = conversion.py2ro(qmethod)
        res = self._write_table(self, **{'file': path, 'quote': quote, 'sep': sep, 
                                         'eol': eol, 'na': na, 'dec': dec,
                                         'row.names': row_names, 
                                         'col.names': col_names, 'qmethod': qmethod, 'append': append})
        return res
    
    def iter_row(self):
        """ iterator across rows """
        for i in xrange(self.nrow):
            yield self.rx(i+1, rinterface.MissingArg)

    def iter_column(self):
        """ iterator across columns """
        for i in xrange(self.ncol):
            yield self.rx(rinterface.MissingArg, i+1)
