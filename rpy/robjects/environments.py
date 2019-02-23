import typing
import rpy2.rinterface as rinterface
from rpy2.robjects.robject import RObjectMixin
from rpy2.robjects import conversion

_new_env = rinterface.baseenv["new.env"]


class Environment(RObjectMixin, rinterface.SexpEnvironment):
    """ An R environement, implementing Python's mapping interface. """

    def __init__(self, o=None):
        if o is None:
            o = _new_env(hash=rinterface.BoolSexpVector([True, ]))
        super(Environment, self).__init__(o)

    def __getitem__(self, item):
        res = super(Environment, self).__getitem__(item)
        res = conversion.converter.rpy2py(res)
        # objects in a R environment have an associated name / symbol
        try:
            res.__rname__ = item
        except AttributeError:
            # the 3rd-party conversion function can return objects
            # for which __rname__ cannot be set (because of fixed
            # __slots__ and no __rname__ in the original set
            # of attributes)
            pass
        return res

    def __setitem__(self, item, value) -> None:
        robj = conversion.converter.py2rpy(value)
        super(Environment, self).__setitem__(item, robj)

    @property
    def enclos(self):
        return conversion.converter.rpy2py(super().enclos)

    @property
    def frame(self):
        return conversion.converter.rpy2py(super().frame)

    def find(self, item, wantfun=False):
        """Find an item, starting with this R environment.

        Raises a `KeyError` if the key cannot be found.

        This method is called `find` because it is somewhat different
        from the method :meth:`get` in Python mappings such :class:`dict`.
        This is looking for a key across enclosing environments, returning
        the first key found.

        :param item: string (name/symbol)
        :rtype: object (as returned by :func:`conversion.converter.rpy2py`)
        """
        res = super(Environment, self).find(item, wantfun=wantfun)
        res = conversion.converter.rpy2py(res)
        # TODO: There is a design issue here. The attribute __rname__ is
        # intended to store the symbol name of the R object but this is
        # meaningless for non-rpy2 objects.
        try:
            res.__rname__ = item
        except AttributeError:
            pass
        return res

    def keys(self) -> typing.Generator[str, None, None]:
        """ Return an iterator over keys in the environment."""
        return super().keys()

    def items(self) -> typing.Generator:
        """ Iterate through the symbols and associated objects in
            this R environment."""
        for k in self:
            yield (k, self[k])

    def values(self) -> typing.Generator:
        """ Iterate through the objects in
            this R environment."""
        for k in self:
            yield self[k]

    def pop(self, k, *args):
        """ E.pop(k[, d]) -> v, remove the specified key
        and return the corresponding value. If the key is not found,
        d is returned if given, otherwise KeyError is raised."""
        if k in self:
            v = self[k]
            del(self[k])
        elif args:
            if len(args) > 1:
                raise ValueError('Invalid number of optional parameters.')
            v = args[0]
        else:
            raise KeyError(k)
        return v

    def popitem(self):
        """ E.popitem() -> (k, v), remove and return some (key, value)
        pair as a 2-tuple; but raise KeyError if E is empty. """
        if len(self) == 0:
            raise KeyError()
        kv = next(self.items())
        del(self[kv[0]])
        return kv

    def clear(self) -> None:
        """ E.clear() -> None.  Remove all items from D. """
        # FIXME: is there a more efficient implementation (when large
        #        number of keys) ?
        for k in self:
            del(self[k])
