"""Containers with R-like behaviors."""

import rpy2.rlike.indexing as rli
import itertools
from typing import Any
from typing import Iterable
from typing import Iterator
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union
import warnings


class OrdDict(dict):
    """ Ordered dictionary.

    Warning: This class is being deprecated. Use
    NamedList instead.

    This is a dict since Python 3.8 `dict` conserve insertion
    order.

    This class differs a little from ordered dicts:
    not all elements have to be named. None as a key value means
    an absence of name for the element.
    """

    __l: List[Tuple[Optional[str], Any]]

    def __init__(self, c: Iterable[Tuple[Optional[str], Any]]=[]):
        warnings.warn(
            'rpy2.rinterface.rlike.container.OrdDict is being deprecated. '
            'Use NamedList instead.',
            DeprecationWarning
        )
        if isinstance(c, TaggedList) or isinstance(c, OrdDict):
            c = c.items()
        elif isinstance(c, dict):
            # FIXME: allow instance from OrdDict ?
            raise TypeError('A regular dictionnary does not ' +
                            'conserve the order of its keys.')

        super(OrdDict, self).__init__()
        self.__l = []

        for k, v in c:
            self[k] = v

    def __copy__(self):
        cp = OrdDict(c=tuple(self.items()))
        return cp

    def __reduce__(self):
        # We need to override the special-cased dict unpickling process in order
        # to retain the attributes the `__l` attribute.
        return (
            self.__class__,  # callable
            (),  # arguments to constructor
            {'_OrdDict__l': self.__l},  # state
            None,  # list items
            iter(self.items()),  # dict items
        )

    def __cmp__(self, o):
        return NotImplemented

    def __eq__(self, o):
        return NotImplemented

    def __getitem__(self, key: str):
        if key is None:
            raise ValueError("Unnamed items cannot be retrieved by key.")
        i = super(OrdDict, self).__getitem__(key)
        return self.__l[i][1]

    def __iter__(self):
        seq = self.__l
        for e in seq:
            k = e[0]
            if k is None:
                continue
            else:
                yield k

    def __len__(self):
        return len(self.__l)

    def __ne__(self, o):
        return NotImplemented

    def __repr__(self) -> str:
        s = ['o{', ]
        for k, v in self.items():
            s.append("'%s': %s, " % (str(k), str(v)))
        s.append('}')
        return ''.join(s)

    def __reversed__(self):
        raise NotImplementedError("Not yet implemented.")

    def __setitem__(self, key: Optional[str], value: Any):
        """ Replace the element if the key is known,
        and conserve its rank in the list, or append
        it if unknown. """

        if key is None:
            self.__l.append((key, value))
            return

        if key in self:
            i = self.index(key)
            self.__l[i] = (key, value)
        else:
            self.__l.append((key, value))
            super(OrdDict, self).__setitem__(key, len(self.__l)-1)

    def byindex(self, i: int) -> Any:
        """ Fetch a value by index (rank), rather than by key."""
        return self.__l[i]

    def index(self, k: str) -> int:
        """ Return the index (rank) for the key 'k' """
        return super(OrdDict, self).__getitem__(k)

    def get(self, k: str, d: Any = None):
        """ OD.get(k[,d]) -> OD[k] if k in OD, else d.  d defaults to None """
        try:
            res = self[k]
        except KeyError:
            res = d
        return res

    def items(self):
        """ OD.items() -> an iterator over the (key, value) items of D """
        return iter(self.__l)

    def keys(self):
        """ """
        return tuple([x[0] for x in self.__l])

    def reverse(self):
        """ Reverse the order of the elements in-place (no copy)."""
        seq = self.__l
        n = len(self.__l)
        for i in range(n//2):
            tmp = seq[i]
            seq[i] = seq[n-i-1]
            kv = seq[i]
            if kv is not None:
                super(OrdDict, self).__setitem__(kv[0], i)
            seq[n-i-1] = tmp
            kv = tmp
            if kv is not None:
                super(OrdDict, self).__setitem__(kv[0], n-i-1)

    def sort(self, cmp=None, key=None, reverse=False):
        raise NotImplementedError("Not yet implemented.")

    def values(self):
        """ """
        return tuple([x[1] for x in self.__l])


class NamedList:
    """ A list for which each item might have a 'name'.

    This is intended to mimic R's lists or pairlists.
    This structure is like a Python list to which optional
    names for each element in the list is added.

    :param seq: an iterable.
    :param names: optional sequence of names
    :param tags: [deprecated] optional sequence of names 
    """

    __list: List
    __names: List[Optional[str]]

    def __init__(self, seq: Iterable,
                 names: Optional[Iterable] = None,
                 tags: Optional[Iterable] = None):
        if tags:
            warnings.warn(
                'The named argument "tags" when constructing '
                'a NamedList is deprecated. Use "names" instead.',
                DeprecationWarning
            )
            if names:
                raise ValueError(
                    '"tags" is deprecated. Only use the named argument '
                    '"names".'
                )
            names = tags
        self.__list = list(seq)
        if names is None:
            names = [None, ] * len(self)
        self.__names = list(names)
        if len(self.__names) != len(self):
            raise ValueError("There must be as many names as seq")

    def __add__(self, tl: 'NamedList'):
        res = NamedList(itertools.chain(self.values(), tl.values()),
                        names=itertools.chain(self.iternames(), tl.iternames()))
        return res

    def __delitem__(self, y):
        self.__list.__delitem__(y)
        self.__names.__delitem__(y)

    def __delslice__(self, i, j):
        self.__list.__delslice__(i, j)
        self.__names.__delslice__(i, j)

    def __iadd__(self, y: 'Union[NamedList, list]'):
        if isinstance(y, NamedList):
            self.__list.__iadd__(tuple(y.values()))
            self.__names.__iadd__(tuple(y.iternames()))
        else:
            self.__list.__iadd__(y)
            self.__names.__iadd__([None, ] * len(y))
        return self

    def __imul__(self, y):
        restags = self.__names.__imul__(y)
        resitems = self.__list.__imul__(y)
        return self

    def __len__(self) -> int:
        return len(self.__list)

    def __mul__(self, y):
        names = self.__names__ * y.__names__
        values = self.__list.__mul__(y)
        return type(self)(values, names=names)

    def __reduce__(self):
        return self.__list.__reduce__()

    @staticmethod
    def from_items(
            namesvalues: Iterable[Tuple[Any, Any]]
    ) -> 'NamedList':
        """Create a NamedList from an iterable of (name, value) pairs."""
        res = NamedList([])
        for n, v in namesvalues:
            res.append(v, name=v)
        return res

    def __getitem__(self, i: Union[int, slice]):
        if isinstance(i, slice):
            return super(self).__init__(self.__list[i],
                                        self.__names[i])
        else:
            return self.__list[i]
            
    def __setitem__(self, i: Union[int, slice],
                    y: 'Union[NamedList, list]'):
        if isinstance(i, slice):
            step = i.step if i.step else 1
            if len(y) != ((i.stop-i.start) // step):
                raise ValueError('Length mistmatch between slice and values.')
            if isinstance(y, NamedList):
                iter_i_name_value = zip(
                    range(i.start, i.stop, step),
                    y.iternames(),
                    y.values()
                )
            elif isinstance(y, list):
                iter_i_name_value = zip(
                    range(i.start, i.stop, step),
                    y,
                    self.__names[i]
                )                
            else:
                raise ValueError('y must be a NamedList or a list.')
            for idx, name, value in iter_i_name_value:
                self.__list[idx] = name
                self.__names[idx] = value                
        else:
            if len(y) != 1:
                raise ValueError('New item must be a NamedList of length 1.')
            self.__list[i] = next(y.values())
            self.__names[i] = next(y.iternames())

    def append(self, obj, name=None, tag=None):
        """ Append an object to the list
        :param obj: object
        :param name: str
        """
        if tag:
            warnings.warn(
                'The named argument "tag" when appending to '
                'a NamedList is deprecated. Use "name" instead.',
                DeprecationWarning
            )
            if name:
                raise ValueError(
                    '"tag" is deprecated. Only use the named argument '
                    '"name".'
                )
        self.__list.append(obj)
        self.__names.append(tag)

    def extend(self, lst: 'Union[NamedList, list]'):
        """ Extend the named list.

        :param lst: A NamedList or list
        """

        if isinstance(lst, NamedList):
            iternames = lst.iternames()
            itervalues = lst.values()
        else:
            iternames = itertools.repeat(None, len(lst))
            itervalues = iter(lst)

        for name, value in zip(iternames, itervalues):
            self.__list.append(value)
            self.__names.append(name)

    def insert(self, index, obj, name=None, tag=None):
        """
        Insert an object in the list

        :param index: integer
        :param obj: object
        :param name: object
        :param tag: object
        """
        if tag:
            warnings.warn(
                'The named argument "tag" is deprecated. '
                'Use "name" instead.',
                DeprecationWarning
            )
            if name:
                raise ValueError(
                    '"tag" is deprecated. Only use the named argument '
                    '"name".'
                )
            name = tag
        self.__list.insert(index, obj)
        self.__names.insert(index, name)

    def iterontag(self, tag):
        """
        iterate on items marked with one given tag.

        :param tag: object
        """
        warnings.warn(
            'The method iterontag is deprecated. '
            'Use items() and filter on the names.',
            DeprecationWarning
        )
        i = 0
        for onetag in self.__names:
            if tag == onetag:
                yield self[i]
            i += 1

    def items(self) -> Iterator[Tuple[Any, Any]]:
        """
        Return an iterator over (name, value) pairs. """
        for name, value in zip(self.__names, self.__list):
            yield (name, value)

    def iternames(self) -> Iterator[Any]:
        for n in self.__names:
            yield n

    def values(self) -> Iterator[Any]:
        for v in self.__list:
            yield v

    def __iter__(self):
        return self.values()

    def itertags(self) -> Iterator[Any]:
        """
        iterate on tags.

        :rtype: iterator
        """
        warnings.warn(
            'The method itertags() is deprecated. '
            'Use iternames() instead.',
            DeprecationWarning
        )
        for tag in self.__names:
            yield tag

    def pop(self, index=None):
        """
        Pop the item at a given index out of the list

        :param index: integer

        """
        if index is None:
            index = len(self) - 1

        res = self.__list.pop(index)
        self.__names.pop(index)
        return res

    def remove(self, value):
        """
        Remove a given value from the list.

        :param value: object

        """
        found = False
        for i in range(len(self)):
            if self.__list[i] == value:
                found = True
                break
        if found:
            self.pop(i)

    def reverse(self):
        """ Reverse the order of the elements in the list. """
        self.__list.reverse()
        self.__names.reverse()

    def sort(self, reverse=False):
        """
        Sort in place
        """
        o = rli.order(self, reverse=reverse)
        self.__list.sort(reverse=reverse)
        self.__names = [self.__names[i] for i in o]

    def __get_names(self):
        return tuple(self.__names)

    def __set_names(self, names):
        if len(names) == len(self.__names):
            self.__names = list(names)
        else:
            raise ValueError('The new sequence of names should have the '
                             'same length as the old one.')

    names = property(__get_names, __set_names)

    def __get_tags(self):
        warnings.warn(
            'The attribute .tags is deprecated. '
            'Use .names instead.',
            DeprecationWarning
        )
        return self.names

    def __set_tags(self, names):
        warnings.warn(
            'The attribute .tags is deprecated. '
            'Use .setname() instead.',
            DeprecationWarning       
        )
        self.names = names

    tags = property(__get_tags, __set_tags)

    def setname(self, i: Union[int, slice], n: Any):
        """
        Set name 'n' for item at index 'i'.

        :param i: int or slice.

        :param n: object (name(s))
        """
        if isinstance(i, slice):
            if len(n) != ((i.stop-i.start) // i.step):
                raise ValueError('Length mistmatch between slice and values.')
            for idx, (name, value) in enumerate(
                    zip(
                        range(i.start, i.stop, i.step if i.step else 1),
                        n
                    )
            ):
                self.__names[idx] = value
        else:
            self.__names[i] = n

    def settag(self, i, t):
        warnings.warn(
            'The method settag() is deprecated. '
            'Use setname() instead.',
            DeprecationWarning       
        )
        self.setname(i, t)


class TaggedList(NamedList):

    def __init__(self, *args, **kwargs):
        warnings.warn('The class name "TaggedList" is deprecated. '
                      'use "NamedList" instead.', DeprecationWarning)
        super().__init__(self, *args, **kwargs)
