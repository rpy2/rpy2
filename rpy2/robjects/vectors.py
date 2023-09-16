import abc
import collections.abc
from rpy2.robjects.robject import RObjectMixin
import rpy2.rinterface as rinterface
from rpy2.rinterface_lib import sexp
from . import conversion

import rpy2.rlike.container as rlc
import datetime
try:
    import zoneinfo  # type: ignore
except ImportError:
    from backports import zoneinfo  # type: ignore
import copy
import itertools
import math
import os
import jinja2  # type: ignore
import time
import tzlocal

from time import struct_time, mktime
import typing
import warnings

from rpy2.rinterface import (Sexp, ListSexpVector, StrSexpVector,
                             IntSexpVector, ByteSexpVector, BoolSexpVector,
                             ComplexSexpVector, PairlistSexpVector,
                             FloatSexpVector, NA_Real, NA_Integer,
                             NA_Character, NA_Logical, NULL, MissingArg)


globalenv_ri = rinterface.globalenv
baseenv_ri = rinterface.baseenv
r_concat = baseenv_ri['c']
as_character = baseenv_ri['as.character']
utils_ri = baseenv_ri['as.environment'](
    rinterface.StrSexpVector(("package:utils", ))
)

# The default timezone can be used for time or datetime objects.
default_timezone = None


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
        conv_args = [None, ] * (len(args)+1)
        conv_args[0] = self._parent
        cv = conversion.get_conversion()
        for i, x in enumerate(args, 1):
            if x is MissingArg:
                conv_args[i] = x
            else:
                conv_args[i] = cv.py2rpy(x)
        kwargs = copy.copy(kwargs)
        for k, v in kwargs.items():
            kwargs[k] = cv.py2rpy(v)
        fun = self._extractfunction
        res = fun(*conv_args, **kwargs)
        res = cv.rpy2py(res)
        return res

    def __getitem__(self, item):
        res = self(item)
        return res

    def __setitem__(self, item, value):
        """ Assign a given value to a given index position in the vector.
        The index position can either be:
        - an int: x[1] = y
        - a tuple of ints: x[1, 2, 3] = y
        - an item-able object (such as a dict): x[{'i': 1}] = y
        """
        fun = self._replacefunction
        cv = conversion.get_conversion()
        if type(item) is tuple:
            args = list([None, ] * (len(item)+2))
            for i, v in enumerate(item):
                if v is MissingArg:
                    continue
                args[i+1] = cv.py2rpy(v)
            args[-1] = cv.py2rpy(value)
            args[0] = self._parent
            res = fun(*args)
        elif (type(item) is dict) or (type(item) is rlc.TaggedList):
            args = rlc.TaggedList.from_items(item)
            for i, (k, v) in enumerate(args.items()):
                args[i] = cv.py2rpy(v)
            args.append(cv.py2rpy(value), tag=None)
            args.insert(0, self._parent, tag=None)
            res = fun.rcall(tuple(args.items()),
                            globalenv_ri)
        else:
            args = [self._parent,
                    cv.py2rpy(item),
                    cv.py2rpy(value)]
            res = fun(*args)
        # TODO: check refcount and copying
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
    Delegate operations such as __getitem__, __add__, etc...
    to the corresponding R function.
    This permits a convenient coexistence between
    operators on Python sequence object with their R conterparts.
    """

    def __init__(self, parent):
        """ The parent in expected to inherit from Vector. """
        self._parent = parent

    def __add__(self, x):
        cv = conversion.get_conversion()
        res = globalenv_ri.find('+')(self._parent, cv.py2rpy(x))
        return cv.rpy2py(res)

    def __sub__(self, x):
        cv = conversion.get_conversion()
        res = globalenv_ri.find('-')(self._parent, cv.py2rpy(x))
        return cv.rpy2py(res)

    def __matmul__(self, x):
        cv = conversion.get_conversion()
        res = globalenv_ri.find("%*%")(self._parent, cv.py2rpy(x))
        return cv.rpy2py(res)

    def __mul__(self, x):
        cv = conversion.get_conversion()
        res = globalenv_ri.find('*')(self._parent, cv.py2rpy(x))
        return cv.rpy2py(res)

    def __pow__(self, x):
        cv = conversion.get_conversion()
        res = globalenv_ri.find('^')(self._parent, cv.py2rpy(x))
        return cv.rpy2py(res)

    def __floordiv__(self, x):
        cv = conversion.get_conversion()
        res = globalenv_ri.find('%/%')(self._parent, cv.py2rpy(x))
        return cv.rpy2py(res)

    def __truediv__(self, x):
        cv = conversion.get_conversion()
        res = globalenv_ri.find('/')(self._parent, cv.py2rpy(x))
        return cv.rpy2py(res)

    def __mod__(self, x):
        cv = conversion.get_conversion()
        res = globalenv_ri.find('%%')(self._parent, cv.py2rpy(x))
        return cv.rpy2py(res)

    def __or__(self, x):
        cv = conversion.get_conversion()
        res = globalenv_ri.find('|')(self._parent, cv.py2rpy(x))
        return cv.rpy2py(res)

    def __and__(self, x):
        cv = conversion.get_conversion()
        res = globalenv_ri.find('&')(self._parent, cv.py2rpy(x))
        return cv.rpy2py(res)

    def __invert__(self):
        res = globalenv_ri.find('!')(self._parent)
        return conversion.get_conversion().rpy2py(res)

    # Comparisons

    def __lt__(self, x):
        cv = conversion.get_conversion()
        res = globalenv_ri.find('<')(self._parent, cv.py2rpy(x))
        return cv.rpy2py(res)

    def __le__(self, x):
        cv = conversion.get_conversion()
        res = globalenv_ri.find('<=')(self._parent, cv.py2rpy(x))
        return cv.rpy2py(res)

    def __eq__(self, x):
        cv = conversion.get_conversion()
        res = globalenv_ri.find('==')(self._parent, cv.py2rpy(x))
        return cv.rpy2py(res)

    def __ne__(self, x):
        cv = conversion.get_conversion()
        res = globalenv_ri.find('!=')(self._parent, cv.py2rpy(x))
        return cv.rpy2py(res)

    def __gt__(self, x):
        cv = conversion.get_conversion()
        res = globalenv_ri.find('>')(self._parent, cv.py2rpy(x))
        return cv.rpy2py(res)

    def __ge__(self, x):
        cv = conversion.get_conversion()
        res = globalenv_ri.find('>=')(self._parent, cv.py2rpy(x))
        return cv.rpy2py(res)

    def __neg__(self):
        res = globalenv_ri.find('-')(self._parent)
        return res

    def __contains__(self, what):
        res = globalenv_ri.find('%in%')(what, self._parent)
        return res[0]


_sample = rinterface.baseenv['sample']


class Vector(RObjectMixin):
    """Vector(seq) -> Vector.

    The parameter 'seq' can be an instance inheriting from
    rinterface.SexpVector, or an arbitrary Python object.
    In the later case, a conversion will be attempted using
    conversion.get_conversion().py2rpy().

    R vector-like object. Items can be accessed with:

    - the method "__getitem__" ("[" operator)

    - the delegators rx or rx2
    """

    _html_template = jinja2.Template(
        """
        <span>{{ classname }} with {{ nelements }} elements.</span>
        <table>
        <tbody>
          <tr>
          {% for elt in elements %}
            <td>
            {{ elt }}
            </td>
          {% endfor %}
          </tr>
        </tbody>
        </table>
        """)

    def _add_rops(self):
        self.ro = VectorOperationsDelegator(self)
        self.rx = ExtractDelegator(self)
        self.rx2 = DoubleExtractDelegator(self)

    def __add__(self, x):
        cv = conversion.get_conversion()
        res = baseenv_ri.find("c")(self, cv.py2rpy(x))
        res = cv.rpy2py(res)
        return res

    def __getitem__(self, i):
        res = super().__getitem__(i)

        if isinstance(res, Sexp):
            res = conversion.get_conversion().rpy2py(res)
        return res

    def __setitem__(self, i, value):
        value = conversion.get_conversion().py2rpy(value)
        super().__setitem__(i, value)

    @property
    def names(self):
        """Names for the items in the vector."""
        res = super().names
        res = conversion.get_conversion().rpy2py(res)
        return res

    @names.setter
    def names(self, value):
        res = globalenv_ri.find("names<-")(
            self, conversion.get_conversion().py2rpy(value)
        )
        self.__sexp__ = res.__sexp__

    def items(self):
        """ iterator on names and values """
        # TODO: should be a view ?
        if super().names.rsame(rinterface.NULL):
            it_names = itertools.cycle((None, ))
        else:
            it_names = iter(self.names)
        it_self = iter(self)
        for v, k in zip(it_self, it_names):
            yield (k, v)

    def sample(self: collections.abc.Sized, n: int, replace: bool = False,
               probabilities: typing.Optional[collections.abc.Sized] = None):
        """ Draw a random sample of size n from the vector.

        If 'replace' is True, the sampling is done with replacement.
        The optional argument 'probabilities' can indicate sampling
        probabilities."""

        assert isinstance(n, int)
        assert isinstance(replace, bool)
        if probabilities is not None:
            if len(probabilities) != len(self):
                raise ValueError('The sequence of probabilities must '
                                 'match the length of the vector.')
            if not isinstance(probabilities, rinterface.FloatSexpVector):
                probabilities = FloatVector(probabilities)
        res = _sample(self, IntVector((n,)),
                      replace=BoolVector((replace, )),
                      prob=probabilities)
        res = conversion.rpy2py(res)
        return res

    def repr_format_elt(self, elt, max_width=12):
        max_width = int(max_width)
        if elt in (NA_Real, NA_Integer, NA_Character, NA_Logical):
            res = repr(elt)
        elif isinstance(elt, int):
            res = '%8i' % elt
        elif isinstance(elt, float):
            res = '%8f' % elt
        else:
            if isinstance(elt, str):
                elt = repr(elt)
            else:
                elt = type(elt).__name__
            if len(elt) < max_width:
                res = elt
            else:
                res = "%s..." % (str(elt[:(max_width - 3)]))
        return res

    def _iter_formatted(self, max_items=9):
        format_elt = self.repr_format_elt
        ln = len(self)
        half_items = max_items // 2
        if ln == 0:
            return
        elif ln < max_items:
            for elt in conversion.noconversion(self):
                yield format_elt(elt, max_width=math.floor(52 / ln))
        else:
            for elt in conversion.noconversion(self)[:half_items]:
                yield format_elt(elt)
            yield '...'
            for elt in conversion.noconversion(self)[-half_items:]:
                yield format_elt(elt)

    def __repr_content__(self):
        return ''.join(('[', ', '.join(self._iter_formatted()), ']'))

    def __repr__(self):
        return super().__repr__() + os.linesep + \
            self.__repr_content__()

    def _repr_html_(self, max_items=7):
        d = {'elements': self._iter_formatted(max_items=max_items),
             'classname': type(self).__name__,
             'nelements': len(self)}
        html = self._html_template.render(d)
        return html


class StrVector(Vector, StrSexpVector):
    """Vector of string elements

    StrVector(seq) -> StrVector.

    The parameter 'seq' can be an instance inheriting from
    rinterface.SexpVector, or an arbitrary Python sequence.
    In the later case, all elements in the sequence should be either
    strings, or have a str() representation.
    """

    _factorconstructor = rinterface.baseenv['factor']

    NAvalue = rinterface.NA_Character

    def __init__(self, obj):
        super().__init__(obj)
        self._add_rops()

    def factor(self):
        """
        factor() -> FactorVector

        Construct a factor vector from a vector of strings.
        """

        res = self._factorconstructor(self)
        return conversion.rpy2py(res)


class IntVector(Vector, IntSexpVector):
    """ Vector of integer elements
    IntVector(seq) -> IntVector.

    The parameter 'seq' can be an instance inheriting from
    rinterface.SexpVector, or an arbitrary Python sequence.
    In the later case, all elements in the sequence should be either
    integers, or have an int() representation.
    """

    _tabulate = rinterface.baseenv['tabulate']

    NAvalue = rinterface.NA_Integer

    def __init__(self, obj):
        super().__init__(obj)
        self._add_rops()

    def repr_format_elt(self, elt, max_width: int = 8):
        return repr(elt)

    def tabulate(self, nbins=None):
        """ Like the R function tabulate,
        count the number of times integer values are found """
        if nbins is None:
            nbins = max(1, max(self))
        res = self._tabulate(self)
        return conversion.rpy2py(res)


class BoolVector(Vector, BoolSexpVector):
    """ Vector of boolean (logical) elements
    BoolVector(seq) -> BoolVector.

    The parameter 'seq' can be an instance inheriting from
    rinterface.SexpVector, or an arbitrary Python sequence.
    In the later case, all elements in the sequence should be either
    booleans, or have a bool() representation.
    """

    NAvalue = rinterface.NA_Logical

    def __init__(self, obj):
        super().__init__(obj)
        self._add_rops()


class ByteVector(Vector, ByteSexpVector):
    """ Vector of byte elements
    ByteVector(seq) -> ByteVector.

    The parameter 'seq' can be an instance inheriting from
    rinterface.SexpVector, or an arbitrary Python sequence.
    In the later case, all elements in the sequence should be either
    be bytes (integers >= 0 and <= 255).
    """

    def __init__(self, obj):
        super().__init__(obj)
        self._add_rops()


class ComplexVector(Vector, ComplexSexpVector):
    """ Vector of complex elements

    ComplexVector(seq) -> ComplexVector

    The parameter 'seq' can be an instance inheriting from
    rinterface.SexpVector, or an arbitrary Python sequence.
    In the later case, all elements in the sequence should be either
    complex, or have a complex() representation.
    """

    NAvalue = rinterface.NA_Complex

    def __init__(self, obj):
        super().__init__(obj)
        self._add_rops()


class FloatVector(Vector, FloatSexpVector):
    """ Vector of float (double) elements

    FloatVector(seq) -> FloatVector.

    The parameter 'seq' can be an instance inheriting from
    rinterface.SexpVector, or an arbitrary Python sequence.
    In the later case, all elements in the sequence should be either
    float, or have a float() representation.
    """

    NAvalue = rinterface.NA_Real

    def __init__(self, obj):
        super().__init__(obj)
        self._add_rops()


class FactorVector(IntVector):
    """ Vector of 'factors'.

    FactorVector(obj,
                 levels = rinterface.MissingArg,
                 labels = rinterface.MissingArg,
                 exclude = rinterface.MissingArg,
                 ordered = rinterface.MissingArg) -> FactorVector

    obj: StrVector or StrSexpVector
    levels: StrVector or StrSexpVector
    labels: StrVector or StrSexpVector (of same length as levels)
    exclude: StrVector or StrSexpVector
    ordered: boolean

    """

    _factor = baseenv_ri['factor']
    _levels = baseenv_ri['levels']
    _levels_set = baseenv_ri['levels<-']
    _nlevels = baseenv_ri['nlevels']
    _isordered = baseenv_ri['is.ordered']

    NAvalue = rinterface.NA_Integer

    def __init__(self, obj,
                 levels=rinterface.MissingArg,
                 labels=rinterface.MissingArg,
                 exclude=rinterface.MissingArg,
                 ordered=rinterface.MissingArg):
        if not isinstance(obj, Sexp):
            obj = StrSexpVector(obj)
        if ('factor' in obj.rclass) and \
           all(p is rinterface.MissingArg for p in (labels,
                                                    exclude,
                                                    ordered)):
            res = obj
        else:
            res = self._factor(obj,
                               levels=levels,
                               labels=labels,
                               exclude=exclude,
                               ordered=ordered)
        super(FactorVector, self).__init__(res)

    def repr_format_elt(self, elt, max_width=8):
        max_width = int(max_width)
        levels = self._levels(self)
        if elt is NA_Integer:
            res = repr(elt)
        else:
            res = levels[elt-1]
            if len(res) >= max_width:
                res = "%s..." % (res[:(max_width - 3)])
        return res

    def __levels_get(self):
        res = self._levels(self)
        return conversion.rpy2py(res)

    def __levels_set(self, value):
        res = self._levels_set(self,
                               conversion.get_conversion().py2rpy(value))
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

    def iter_labels(self):
        """ Iterate the over the labels, that is iterate over
        the items returning associated label for each item """
        levels = self.levels
        for x in conversion.noconversion(self):
            yield (rinterface.NA_Character if x is rinterface.NA_Integer
                   else levels[x-1])


class PairlistVector(Vector, PairlistSexpVector):
    """R pairlist vector."""
    pass


class ListVector(Vector, ListSexpVector):
    """ R list (vector of arbitray elements)

    ListVector(iterable) -> ListVector.

    The parameter 'iterable' can be:

    - an object with a method `items()`, such for example a dict,
      a rpy2.rlike.container.TaggedList,
      an rpy2.rinterface.SexpVector of type VECSXP.

    - an iterable of (name, value) tuples
    """
    _vector = rinterface.baseenv['vector']

    _html_template = jinja2.Template(
        """
        <span>{{ classname }} with {{ nelements }} elements.</span>
        <table>
        <tbody>
        {% for name, elt in names_elements %}
          <tr>
            <th>
            {{ name }}
            </th>
            <td>
            {{ elt }}
            </td>
          </tr>
        {% endfor %}
        </tbody>
        </table>
        """)

    def __init__(self, tlist):
        if isinstance(tlist, rinterface.ListSexpVector):
            if tlist.typeof != rinterface.RTYPES.VECSXP:
                raise ValueError("tlist should have "
                                 "tlist.typeof == rinterface.RTYPES.VECSXP")
            super().__init__(tlist)
        elif hasattr(tlist, 'items') and callable(tlist.items):
            cv = conversion.get_conversion()
            kv = [(k, cv.py2rpy(v)) for k, v in tlist.items()]
            kv = tuple(kv)
            df = baseenv_ri.find("list").rcall(kv, globalenv_ri)
            super().__init__(df)
        elif hasattr(tlist, "__iter__"):
            if not callable(tlist.__iter__):
                raise ValueError('tlist should have a /method/ __iter__ '
                                 '(not an attribute)')
            cv = conversion.get_conversion()
            kv = [(str(k), cv.py2rpy(v)) for k, v in tlist]
            kv = tuple(kv)
            df = baseenv_ri.find("list").rcall(kv, globalenv_ri)
            super().__init__(df)
        else:
            raise ValueError('tlist can only be either an iter-able or an '
                             'instance of rpy2.rinterface.ListSexpVector, '
                             'of R type VECSXP, or a Python dict.')
        self._add_rops()

    def _iter_repr(self, max_items=9):
        if len(self) <= max_items:
            for elt in conversion.noconversion(self):
                yield elt
        else:
            half_items = max_items // 2
            for i in range(0, half_items):
                yield self[i]
            yield '...'
            for i in range(-half_items, 0):
                yield self[i]

    def __repr__(self):
        res = []
        for i, elt in enumerate(self._iter_repr()):
            if isinstance(elt, ListVector):
                res.append(super().__repr__())
            elif isinstance(elt, str) and elt == '...':
                res.append(elt)
            else:
                try:
                    name = self.names[i]
                except TypeError:
                    name = '<no name>'
                res.append("  %s: %s%s  %s"
                           % (name,
                              type(elt),
                              os.linesep,
                              elt.__repr__()))

        res = super().__repr__() + os.linesep + \
            os.linesep.join(res)
        return res

    def _repr_html_(self, max_items=7):
        elements = list()
        for e in self._iter_repr(max_items=max_items):
            if hasattr(e, '_repr_html_'):
                elements.append(e._repr_html_())
            else:
                elements.append(e)

        names = list()
        rnames = self.names
        rnames_null = rinterface.NULL.rsame(rnames)
        if len(self) <= max_items:
            names.extend(
                rnames
                if not rnames_null
                else ['[no name]'] * len(self)
            )
        else:
            half_items = max_items // 2
            for i in range(0, half_items):
                try:
                    name = (rnames[i]
                            if not rnames_null else '[no name]')
                except TypeError:
                    name = '[no name]'
                names.append(name)
            names.append('...')
            for i in range(-half_items, 0):
                try:
                    name = rnames[i]
                except TypeError:
                    name = '[no name]'
                names.append(name)

        d = {'names_elements': zip(names, elements),
             'nelements': len(self),
             'classname': type(self).__name__}
        html = self._html_template.render(d)
        return html

    @classmethod
    def from_length(cls, length):
        """ Create a list of given length """
        res = ListVector._vector(StrSexpVector(("list", )), length)
        res = cls(res)
        return res


class POSIXt(abc.ABC):
    """ POSIX time vector. This is an abstract class. """

    def repr_format_elt(self, elt, max_width=12):
        max_width = int(max_width)
        str_elt = str(elt)
        if len(str_elt) < max_width:
            res = elt
        else:
            res = "%s..." % str_elt[:(max_width - 3)]
        return res

    def _iter_formatted(self, max_items=9):
        ln = len(self)
        half_items = max_items // 2
        if ln == 0:
            return
        elif ln < max_items:
            str_vec = StrVector(as_character(self))
        else:
            str_vec = r_concat(
                as_character(
                  self.rx(IntSexpVector(tuple(range(1, (half_items-1)))))
                ),
                StrSexpVector(['...']),
                as_character(
                  self.rx(IntSexpVector(tuple(range((ln-half_items), ln))))
                ))
        for str_elt in str_vec:
            yield self.repr_format_elt(str_elt)


class POSIXlt(POSIXt, ListVector):
    """ Representation of dates with a 11-component structure
    (similar to Python's time.struct_time).

    POSIXlt(seq) -> POSIXlt.

    The constructor accepts either an R vector
    or a sequence (an object with the Python
    sequence interface) of time.struct_time objects.
    """

    _expected_colnames = {
        x: i for i, x in enumerate(
            ('sec', 'min', 'hour', 'mday', 'mon', 'year',
             'wday', 'yday', 'isdst', 'zone', 'gmtoff'))
    }
    # R starts the week on Sunday while Python starts it on Monday
    _wday_r_to_py = (6, 0, 1, 2, 3, 4, 5)

    def __init__(self, seq):
        """
        """
        if isinstance(seq, Sexp):
            super()(seq)
        else:
            for elt in conversion.noconversion(seq):
                if not isinstance(elt, struct_time):
                    raise ValueError(
                        'All elements must inherit from time.struct_time'
                    )
            as_posixlt = baseenv_ri['as.POSIXlt']
            origin = StrSexpVector([time.strftime("%Y-%m-%d",
                                                  time.gmtime(0)), ])
            rvec = FloatSexpVector([mktime(x) for x in seq])
            sexp = as_posixlt(rvec, origin=origin)
            super().__init__(sexp)

    def __getitem__(self, i):
        # "[[" operator returns the components of a time object
        # (and yes, this is confusing)
        aslist = ListVector(self)
        idx = self._expected_colnames
        seq = (aslist[idx['year']][i]+1900,
               aslist[idx['mon']][i]+1,
               aslist[idx['mday']][i],
               aslist[idx['hour']][i],
               aslist[idx['min']][i],
               aslist[idx['sec']][i],
               self._wday_r_to_py[aslist[idx['wday']][i]],
               aslist[idx['yday']][i]+1,
               aslist[idx['isdst']][i])
        return struct_time(
            seq,
            {'tm_zone': aslist[idx['zone']][i],
             'tmp_gmtoff': aslist[idx['gmtoff']][i]}
        )

    def __repr__(self):
        return super(Sexp, self).__repr__()


def get_timezone():
    """Return the system's timezone settings."""
    if default_timezone:
        timezone = default_timezone
    else:
        timezone = tzlocal.get_localzone()
    return timezone


class DateVector(FloatVector):
    """ Representation of dates as number of days since 1/1/1970.

    Date(seq) -> Date.

    The constructor accepts either an R vector floats
    or a sequence (an object with the Python
    sequence interface) of time.struct_time objects.
    """

    def __init__(self, seq):
        """ Create a POSIXct from either an R vector or a sequence
        of Python datetime.date objects.
        """

        if isinstance(seq, Sexp):
            init_param = seq
        elif isinstance(seq[0], datetime.date):
            init_param = DateVector.sexp_from_date(seq)
        else:
            raise TypeError(
                'Unable to create an R Date vector from objects of type %s' %
                type(seq))
        super().__init__(init_param)

    @classmethod
    def sexp_from_date(cls, seq):
        return cls(FloatVector([x.toordinal() for x in seq]))

    @staticmethod
    def isrinstance(obj) -> bool:
        """Return whether an R object an instance of Date."""
        return obj.rclass[-1] == 'Date'


class POSIXct(POSIXt, FloatVector):
    """ Representation of dates as seconds since Epoch.
    This form is preferred to POSIXlt for inclusion in a DataFrame.

    POSIXlt(seq) -> POSIXlt.

    The constructor accepts either an R vector floats
    or a sequence (an object with the Python
    sequence interface) of time.struct_time objects.
    """

    _as_posixct = baseenv_ri['as.POSIXct']
    _ISOdatetime = baseenv_ri['ISOdatetime']

    def __init__(self, seq):
        """ Create a POSIXct from either an R vector or a sequence
        of Python dates.
        """

        if isinstance(seq, Sexp):
            init_param = seq
        elif isinstance(seq[0], struct_time):
            init_param = POSIXct.sexp_from_struct_time(seq)
        elif isinstance(seq[0], datetime.datetime):
            init_param = POSIXct.sexp_from_datetime(seq)
        else:
            raise TypeError(
                'All elements must inherit from time.struct_time or '
                'datetime.datetime.')
        super().__init__(init_param)

    @staticmethod
    def _sexp_from_seq(seq, tz_info_getter, isodatetime_columns):
        """ return a POSIXct vector from a sequence of time.struct_time
        elements. """
        tz_count = 0
        tz_info = None
        for elt in conversion.noconversion(seq):
            tmp = tz_info_getter(elt)
            if tz_info is None:
                tz_info = tmp
                tz_count = 1
            elif tz_info == tmp:
                tz_count += 1
            else:
                # different time zones
                # TODO: create a list of time zones with tz_count times
                # tz_info, add the current tz_info and append further.
                raise ValueError(
                    'Sequences of dates with different time zones not '
                    'yet allowed.'
                )

        if tz_info is None:
            tz_info = default_timezone if default_timezone else ''
        # We could use R's as.POSIXct instead of ISOdatetime
        # since as.POSIXct is used by it anyway, but the overall
        # interface for dates and conversion between formats
        # is not exactly straightforward. Someone with more
        # time should look into this.

        d = isodatetime_columns(seq)
        sexp = POSIXct._ISOdatetime(
            *d,
            tz=StrSexpVector((str(tz_info), ))
        )
        return sexp

    @staticmethod
    def sexp_from_struct_time(seq):
        def f(seq):
            return [IntVector([x.tm_year for x in seq]),
                    IntVector([x.tm_mon for x in seq]),
                    IntVector([x.tm_mday for x in seq]),
                    IntVector([x.tm_hour for x in seq]),
                    IntVector([x.tm_min for x in seq]),
                    IntVector([x.tm_sec for x in seq])]
        return POSIXct._sexp_from_seq(seq, lambda elt: elt.tm_zone, f)

    @staticmethod
    def sexp_from_datetime(seq):
        """ return a POSIXct vector from a sequence of
        datetime.datetime elements. """
        def f(seq):
            return [IntVector([x.year for x in seq]),
                    IntVector([x.month for x in seq]),
                    IntVector([x.day for x in seq]),
                    IntVector([x.hour for x in seq]),
                    IntVector([x.minute for x in seq]),
                    IntVector([x.second for x in seq])]

        def get_tz(elt):
            return elt.tzinfo if elt.tzinfo else None

        return POSIXct._sexp_from_seq(seq, get_tz, f)

    @staticmethod
    def isrinstance(obj) -> bool:
        """Is an R object an instance of POSIXct."""
        return obj.rclass[0] == 'POSIXct'

    @staticmethod
    def _datetime_from_timestamp(ts, tz) -> datetime.datetime:
        """Platform-dependent conversion from timestamp to datetime"""
        if os.name != 'nt' or ts > 0:
            return datetime.datetime.fromtimestamp(ts, tz)
        else:
            dt_utc = (datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc) +
                      datetime.timedelta(seconds=ts))
            dt = dt_utc.replace(tzinfo=tz)
            offset = dt.utcoffset()
            if offset is None:
                return dt
            else:
                return dt + offset

    def iter_localized_datetime(self):
        """Iterator yielding localized Python datetime objects."""
        try:
            r_tzone_name = self.do_slot('tzone')[0]
        except LookupError:
            warnings.warn('R object inheriting from "POSIXct" but without '
                          'attribute "tzone".')
            r_tzone_name = ''
        if r_tzone_name == '':
            # R is implicitly using the local timezone, while Python
            # time libraries will assume UTC.
            r_tzone = get_timezone()
        else:
            r_tzone = zoneinfo.ZoneInfo(r_tzone_name)
        for x in self:
            yield (
                None if math.isnan(x)
                else POSIXct._datetime_from_timestamp(x, r_tzone)
            )


class Array(Vector):
    """ An R array """
    _dimnames_get = baseenv_ri['dimnames']
    _dimnames_set = baseenv_ri['dimnames<-']
    _dim_get = baseenv_ri['dim']
    _dim_set = baseenv_ri['dim<-']
    _isarray = baseenv_ri['is.array']

    def __dim_get(self):
        res = self._dim_get(self)
        res = conversion.get_conversion().rpy2py(res)
        return res

    def __dim_set(self, value):
        # TODO: R will create a copy of the object upon assignment
        #   of a new dimension attribute.
        raise NotImplementedError("Not yet implemented")
        value = conversion.get_conversion().py2rpy(value)
        self._dim_set(self, value)

    dim = property(__dim_get, __dim_set, None,
                   "Get or set the dimension of the array.")

    @property
    def names(self) -> sexp.Sexp:
        """ Return a list of name vectors
        (like the R function 'dimnames' does)."""

        res = self._dimnames_get(self)
        res = conversion.get_conversion().rpy2py(res)
        return res

    @names.setter
    def names(self, value) -> None:
        """ Set list of name vectors
        (like the R function 'dimnames' does)."""

        value = conversion.get_conversion().rpy2py(value)
        res = self._dimnames_set(self, value)
        self.__sexp__ = res.__sexp__

    dimnames = names


class IntArray(Array, IntVector):
    pass


class ByteArray(Array, ByteVector):
    pass


class FloatArray(Array, FloatVector):
    pass


class BoolArray(Array, BoolVector):
    pass


class ComplexArray(Array, ComplexVector):
    pass


class StrArray(Array, StrVector):
    pass


class Matrix(Array):
    """ An R matrix """
    _transpose = baseenv_ri['t']
    _rownames = baseenv_ri['rownames']
    _colnames = baseenv_ri['colnames']
    _dot = baseenv_ri['%*%']
    _matmul = baseenv_ri['%*%']
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
        return conversion.get_conversion().rpy2py(res)

    def __rownames_set(self, rn):
        if isinstance(rn, StrSexpVector):
            if len(rn) != self.nrow:
                raise ValueError('Invalid length.')
            if self.dimnames is NULL:
                dn = ListVector.from_length(2)
                dn[0] = rn
                self.do_slot_assign('dimnames', dn)
            else:
                dn = self.dimnames
                dn[0] = rn
        else:
            raise ValueError(
                'The rownames attribute can only be an R string vector.'
            )

    rownames = property(__rownames_get, __rownames_set, None, "Row names")

    def __colnames_get(self):
        """ Column names

        :rtype: SexpVector
        """
        res = self._colnames(self)
        return conversion.get_conversion().rpy2py(res)

    def __colnames_set(self, cn):
        if isinstance(cn, StrSexpVector):
            if len(cn) != self.ncol:
                raise ValueError('Invalid length.')
            if self.dimnames is NULL:
                dn = ListVector.from_length(2)
                dn[1] = cn
                self.do_slot_assign('dimnames', dn)
            else:
                dn = self.dimnames
                dn[1] = cn
        else:
            raise ValueError(
                'The colnames attribute can only be an R string vector.'
            )

    colnames = property(__colnames_get, __colnames_set, None, "Column names")

    def transpose(self):
        """ transpose the matrix """
        res = self._transpose(self)
        return conversion.get_conversion().rpy2py(res)

    def __matmul__(self, x):
        """ Matrix multiplication. """
        cv = conversion.get_conversion()
        res = self._matmul(self, cv.py2rpy(x))
        return cv.rpy2py(res)

    def crossprod(self, m):
        """ crossproduct X'.Y"""
        cv = conversion.get_conversion()
        res = self._crossprod(self, cv.rpy2py(m))
        return cv.rpy2py(res)

    def tcrossprod(self, m):
        """ crossproduct X.Y'"""
        res = self._tcrossprod(self, m)
        return conversion.get_conversion().rpy2py(res)

    def svd(self, nu=None, nv=None, linpack=False):
        """ SVD decomposition.
        If nu is None, it is given the default value min(tuple(self.dim)).
        If nv is None, it is given the default value min(tuple(self.dim)).
        """
        if nu is None:
            nu = min(tuple(self.dim))
        if nv is None:
            nv = min(tuple(self.dim))
        res = self._svd(self, nu=nu, nv=nv)
        return conversion.get_conversion().rpy2py(res)

    def dot(self, m):
        """ Matrix multiplication """
        res = self._dot(self, m)
        return conversion.get_conversion().rpy2py(res)

    def eigen(self):
        """ Eigen values """
        res = self._eigen(self)
        return conversion.get_conversion().rpy2py(res)


class DataFrame(ListVector):
    """ R 'data.frame'.
    """
    _dataframe_name = rinterface.StrSexpVector(('data.frame',))
    _read_csv = utils_ri['read.csv']
    _write_table = utils_ri['write.table']
    _cbind = rinterface.baseenv['cbind.data.frame']
    _rbind = rinterface.baseenv['rbind.data.frame']
    _is_list = rinterface.baseenv['is.list']

    _html_template = jinja2.Template(
        """
        <span>R/rpy2 DataFrame ({{ nrows }} x {{ ncolumns }})</span>
        <table>
          <thead>
            <tr>
              {% for name in column_names %}
              <th>{{ name }}</th>
              {% endfor %}
            </tr>
          </thead>
          <tbody>
          {% for row_i in rows %}
          <tr>
            {% for col_i in columns %}
            <td>
              {{ elements[col_i][row_i] }}
            </td>
            {% endfor %}
          </tr>
          {% endfor %}
          </tbody>
        </table>
    """)

    def __init__(self, obj, stringsasfactor=False, checknames=False):
        """ Create a new data frame.

        :param obj: object inheriting from rpy2.rinterface.SexpVector,
            or inheriting from TaggedList or a mapping name -> value
        :param stringsasfactors: Boolean indicating whether vectors
            of strings should be turned to vectors. Note that factors
            will not be turned to string vectors.
        :param checknames: Boolean indicating whether column names
            should be transformed to R syntactically valid names.
        """
        if isinstance(obj, rinterface.ListSexpVector):
            if obj.typeof != rinterface.RTYPES.VECSXP:
                raise ValueError(
                    "obj should be of typeof RTYPES.VECSXP "
                    " (and we get %s)" % rinterface.RTYPES(obj.typeof)
                )
            if (
                    self._is_list(obj)[0] or
                    globalenv_ri.find('inherits')(
                        obj, self._dataframe_name
                    )[0]
            ):
                # TODO: is it really a good idea to pass R lists
                # to the constructor ?
                super().__init__(obj)
                return
            else:
                raise ValueError(
                    "When passing R objects to build a DataFrame, "
                    "the R object must be a list or inherit from "
                    "the R class 'data.frame'."
                )
        elif isinstance(obj, rlc.TaggedList):
            cv = conversion.get_conversion()
            kv = [(k, cv.py2rpy(v)) for k, v in obj.items()]
        else:
            cv = conversion.get_conversion()
            try:
                kv = [(str(k), cv.py2rpy(v)) for k, v in obj.items()]
            except AttributeError:
                raise ValueError(
                    'obj can only be'
                    'an instance of rpy2.rinterface.ListSexpVector, '
                    'an instance of TaggedList, '
                    'or an objects with a methods items() that returns '
                    '(key, value) pairs '
                    '(such a Python dict, rpy2.rlike.container OrdDict).')

        # Check if there is a conflicting column name
        if 'stringsAsFactors' in (k for k, v in kv):
            warnings.warn('The column name "stringsAsFactors" is '
                          'conflicting with named parameter '
                          'in underlying R function "data.frame()".')
        else:
            kv.extend((('stringsAsFactors', stringsasfactor),
                       ('check.names', checknames)))

        # Call R's data frame constructor
        kv = tuple(kv)
        df = baseenv_ri.find("data.frame").rcall(kv, globalenv_ri)
        super().__init__(df)

    def _repr_html_(self, max_items=7):
        names = list()
        if len(self) <= max_items:
            names.extend(self.names)
        else:
            half_items = max_items // 2
            for i in range(0, half_items):
                try:
                    name = self.names[i]
                except TypeError:
                    name = '[no name]'
                names.append(name)
            names.append('...')
            for i in range(-half_items, 0):
                try:
                    name = self.names[i]
                except TypeError:
                    name = '[no name]'
                names.append(name)

        elements = list()
        for e in self._iter_repr(max_items=max_items):
            if hasattr(e, '_repr_html_'):
                elements.append(tuple(e._iter_formatted()))
            else:
                elements.append(['...', ])

        d = {'column_names': names,
             'rows': range(len(elements[0]) if len(elements) else 0),
             'columns': tuple(range(len(names))),
             'nrows': self.nrow,
             'ncolumns': self.ncol,
             'elements': elements}
        html = self._html_template.render(d)
        return html

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
        return conversion.get_conversion().rpy2py(res)

    def _set_rownames(self, rownames):
        res = baseenv_ri["rownames<-"](
            self, conversion.get_conversion().py2rpy(rownames)
        )
        self.__sexp__ = res.__sexp__

    rownames = property(_get_rownames, _set_rownames, None,
                        'Row names')

    def _get_colnames(self):
        res = baseenv_ri["colnames"](self)
        return conversion.get_conversion().rpy2py(res)

    def _set_colnames(self, colnames):
        res = baseenv_ri["colnames<-"](
            self, conversion.get_conversion().py2rpy(colnames)
        )
        self.__sexp__ = res.__sexp__

    colnames = property(_get_colnames, _set_colnames, None)

    def __getitem__(self, i):
        # Make sure this is not a List returned

        # 3rd-party conversions could return objects
        # that no longer inherit from rpy2's R objects.
        # We need to use the low-level __getitem__
        # to bypass the conversion mechanism.
        # R's data.frames have no representation at the C-API level
        # (they are lists)
        tmp = rinterface.ListSexpVector.__getitem__(self, i)

        if tmp.typeof == rinterface.RTYPES.VECSXP:
            return DataFrame(tmp)
        else:
            return conversion.get_conversion().rpy2py(tmp)

    def cbind(self, *args, **kwargs):
        """ bind objects as supplementary columns """
        new_args = [self, ] + [conversion.rpy2py(x) for x in args]
        new_kwargs = dict(
            [(k, conversion.rpy2py(v)) for k, v in kwargs.items()]
        )
        res = self._cbind(*new_args, **new_kwargs)
        return conversion.get_conversion().rpy2py(res)

    def rbind(self, *args, **kwargs):
        """ bind objects as supplementary rows """
        new_args = [conversion.rpy2py(x) for x in args]
        new_kwargs = dict(
            [(k, conversion.rpy2py(v)) for k, v in kwargs.items()]
        )
        res = self._rbind(self, *new_args, **new_kwargs)
        return conversion.rpy2py(res)

    def head(self, *args, **kwargs):
        """ Call the R generic 'head()'. """
        res = utils_ri['head'](self, *args, **kwargs)
        return conversion.rpy2py(res)

    @classmethod
    def from_csvfile(cls, path, header=True, sep=',',
                     quote='"', dec='.',
                     row_names=rinterface.MissingArg,
                     col_names=rinterface.MissingArg,
                     fill=True, comment_char='',
                     na_strings=[],
                     as_is=False):
        """ Create an instance from data in a .csv file.

        :param path: string with a path
        :param header: boolean (heading line with column names or not)
        :param sep: separator character
        :param quote: quote character
        :param row_names: column name, or column index for column names
           (warning: indexing starts at one in R)
        :param fill: boolean (fill the lines when less entries than columns)
        :param comment_char: comment character
        :param na_strings: a list of strings which are interpreted to be NA
           values
        :param as_is: boolean (keep the columns of strings as such, or turn
           them into factors)
        """
        cv = conversion.get_conversion()
        path = cv.py2rpy(path)
        header = cv.py2rpy(header)
        sep = cv.py2rpy(sep)
        quote = cv.py2rpy(quote)
        dec = cv.py2rpy(dec)
        if row_names is not rinterface.MissingArg:
            row_names = cv.py2rpy(row_names)
        if col_names is not rinterface.MissingArg:
            col_names = cv.py2rpy(col_names)
        fill = cv.py2rpy(fill)
        comment_char = cv.py2rpy(comment_char)
        as_is = cv.py2rpy(as_is)
        na_strings = cv.py2rpy(na_strings)
        res = DataFrame._read_csv(path,
                                  **{'header': header, 'sep': sep,
                                     'quote': quote, 'dec': dec,
                                     'row.names': row_names,
                                     'col.names': col_names,
                                     'fill': fill,
                                     'comment.char': comment_char,
                                     'na.strings': na_strings,
                                     'as.is': as_is})
        return cls(res)

    def to_csvfile(self, path, quote=True, sep=',',
                   eol=os.linesep, na='NA', dec='.',
                   row_names=True, col_names=True,
                   qmethod='escape', append=False):
        """ Save the data into a .csv file.

        :param path         : string with a path
        :param quote        : quote character
        :param sep          : separator character
        :param eol          : end-of-line character(s)
        :param na           : string for missing values
        :param dec          : string for decimal separator
        :param row_names    : boolean (save row names, or not)
        :param col_names    : boolean (save column names, or not)
        :param comment_char : method to 'escape' special characters
        :param append       : boolean (append if the file in the path is
        already existing, or not)
        """
        cv = conversion.get_conversion()
        path = cv.py2rpy(path)
        append = cv.py2rpy(append)
        sep = cv.py2rpy(sep)
        eol = cv.py2rpy(eol)
        na = cv.py2rpy(na)
        dec = cv.py2rpy(dec)
        row_names = cv.py2rpy(row_names)
        col_names = cv.py2rpy(col_names)
        qmethod = cv.py2rpy(qmethod)
        res = self._write_table(
            self,
            **{'file': path,
               'quote': quote, 'sep': sep,
               'eol': eol, 'na': na, 'dec': dec,
               'row.names': row_names,
               'col.names': col_names, 'qmethod': qmethod,
               'append': append})
        return res

    def iter_row(self):
        """ iterator across rows """
        for i in range(self.nrow):
            yield self.rx(i+1, rinterface.MissingArg)

    def iter_column(self):
        """ iterator across columns """
        for i in range(self.ncol):
            yield self.rx(rinterface.MissingArg, i+1)


class IntMatrix(Matrix, IntVector):
    pass


class ByteMatrix(Matrix, ByteVector):
    pass


class FloatMatrix(Matrix, FloatVector):
    pass


class BoolMatrix(Matrix, BoolVector):
    pass


class ComplexMatrix(Matrix, ComplexVector):
    pass


class StrMatrix(Matrix, StrVector):
    pass


rtypeof2rotype = {
    rinterface.RTYPES.INTSXP: IntVector,
    rinterface.RTYPES.REALSXP: FloatVector,
    rinterface.RTYPES.STRSXP: StrVector,
    rinterface.RTYPES.CPLXSXP: ComplexVector,
    rinterface.RTYPES.LGLSXP: BoolVector
}
