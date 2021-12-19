import contextlib
import os
import typing
import rpy2.rinterface as rinterface
import rpy2.rinterface_lib.sexp as sexp
from rpy2.robjects.robject import RObjectMixin
from rpy2.robjects import conversion

_new_env = rinterface.baseenv["new.env"]


class Environment(RObjectMixin, sexp.SexpEnvironment):
    """ An R environement, implementing Python's mapping interface. """

    def __init__(self, o: typing.Optional[sexp.SexpEnvironment] = None):
        if o is None:
            o = _new_env(hash=rinterface.BoolSexpVector([True, ]))
        super(sexp.SexpEnvironment, self).__init__(o)

    def __getitem__(self, item: str):
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

    def __setitem__(self, item: str, value: typing.Any) -> None:
        robj = conversion.converter.py2rpy(value)
        super(Environment, self).__setitem__(item, robj)

    @property
    def enclos(self) -> typing.Union[sexp.SexpEnvironment, sexp.NULLType]:
        return conversion.converter.rpy2py(super().enclos)

    @enclos.setter
    def enclos(self, value: sexp.SexpEnvironment) -> None:
        # TODO: I can't figure out why mypy is throwing an error
        # here. There scope of this assignment is rather limited
        # (the setter in the parent class SexpEnvironment has the same
        # signature).
        super().enclos = value  # type: ignore

    @property
    def frame(self) -> sexp.SexpEnvironment:
        return conversion.converter.rpy2py(super().frame)

    def find(self, item: str, wantfun: bool = False):
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

    def items(self) -> typing.Generator[
            typing.Tuple[str, sexp.Sexp],
            None, None]:
        """ Iterate through the symbols and associated objects in
            this R environment."""
        for k, v in zip(self.keys(), self.values()):
            yield (k, v)

    def values(self) -> typing.Generator[sexp.Sexp, None, None]:
        """ Iterate through the objects in
            this R environment."""
        for k in self:
            yield self[k]

    def pop(self, k: str, *args) -> sexp.Sexp:
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

    def popitem(self) -> typing.Tuple[str, sexp.Sexp]:
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

    def __repr__(self):
        return os.linesep.join(
            (super(Environment, self).__repr__(),
             'n items: {:d}'.format(len(self)))
        )


@contextlib.contextmanager
def local_context(
        env: typing.Optional[sexp.SexpEnvironment] = None,
        use_rlock: bool = True
) -> typing.Iterator[Environment]:
    """Local context for the evaluation of R code.

    This is a wrapper around the rpy2.rinterface function with the
    same name.

    Args:
    - env: an environment to use as a context. If not specified (None, the
      default), a child environment to the current context is created.
    - use_rlock: whether to use a threading lock (see the documentation about
      "rlock". The default is True.

    Returns:
    Yield the environment (passed to env, or created).
    """
    with rinterface.local_context(env=env, use_rlock=use_rlock) as lc:
        yield Environment(lc)
