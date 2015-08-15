import rpy2.rinterface as rinterface
from rpy2.robjects.robject import RObjectMixin, RObject
from rpy2.robjects import conversion

_new_env = rinterface.baseenv["new.env"]

class Environment(RObjectMixin, rinterface.SexpEnvironment):
    """ An R environement. """
    
    def __init__(self, o=None):
        if o is None:
            o = _new_env(hash=rinterface.SexpVector([True, ], 
                                                    rinterface.LGLSXP))
        super(Environment, self).__init__(o)

    def __getitem__(self, item):
        res = super(Environment, self).__getitem__(item)
        res = conversion.converter.ri2ro(res)
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

    def __setitem__(self, item, value):
        robj = conversion.converter.py2ri(value)
        super(Environment, self).__setitem__(item, robj)

    def get(self, item, wantfun = False):
        """ Get a object from its R name/symol
        :param item: string (name/symbol)
        :rtype: object (as returned by :func:`conversion.converter.ri2ro`)
        """
        res = super(Environment, self).get(item, wantfun = wantfun)
        res = conversion.converter.ri2ro(res)
        res.__rname__ = item
        return res

    def keys(self):
        """ Return a tuple listing the keys in the object """
        return tuple([x for x in self])

    def items(self):
        """ Iterate through the symbols and associated objects in
            this R environment."""
        for k in self:
            yield (k, self[k])
