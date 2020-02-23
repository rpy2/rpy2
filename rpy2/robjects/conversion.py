"""
The module contains the conversions to be
used by rpy2.robjects functions and methods.

Conversions are initially empty place-holders,
raising a NotImplementedError exception.
"""

from functools import singledispatch
import rpy2.rinterface_lib.sexp
import rpy2.rinterface_lib.conversion
import rpy2.rinterface


class NameClassMap(object):
    """Map a name (R class name) to a Python class."""

    default = property(lambda self: self._default)

    def __init__(self, defaultcls):
        self._default = defaultcls
        self._map = dict()

    def __contains__(self, key: str):
        return key in self._map

    def __delitem__(self, key: str):
        del self._map[key]

    def __getitem__(self, key: str):
        return self._map[key]

    def __setitem__(self, key: str, value):
        if not issubclass(value, self._default):
            raise ValueError(
                'The new class must be a subclass of {}'
                '(and {} is not)'
                .format(self._default, value))
        self._map[key] = value

    def find_key(self, keys):
        """
        Find the first mapping key in a sequence of names (keys).

        Args:
          keys (iterable): The keys are the R classes (the last being the
            most distant ancestor class)
        Returns:
           None if no mapping key.
        """
        for k in keys:
            if k in self._map:
                return k
        return None

    def find(self, keys):
        """Find the first mapping in a sequence of names (keys).

        Returns the default class (specified when creating the
        instance if no mapping key."""
        k = self.find_key(keys)
        if k:
            cls = self._map[k]
        else:
            cls = self._default
        return cls


class NameClassMapContext(object):

    def __init__(self, nameclassmap: NameClassMap,
                 d: dict):
        self._nameclassmap = nameclassmap
        self._d = d
        self._keep = []

    def __enter__(self):
        nameclassmap = self._nameclassmap
        for k, v in self._d.items():
            if k in nameclassmap:
                restore = True
                orig_v = nameclassmap[k]
            else:
                restore = False
                orig_v = None
            self._keep.append((k, restore, orig_v))
            nameclassmap[k] = v

    def __exit__(self, exc_type, exc_val, exc_tb):
        nameclassmap = self._nameclassmap
        for k, restore, orig_v in self._keep:
            if restore:
                nameclassmap[k] = orig_v
            else:
                del(nameclassmap[k])
        return False


def noconversion(obj):
    """
    Bypass robject-level conversion.

    Bypass robject-level conversion, casting the object down to
    rinterface-level rpy2 objects.

    :param obj: Any object
    :return: Either an rinterface-level object or a Python object.
    """
    if isinstance(obj, rpy2.rinterface_lib.sexp.Sexp):
        res = (rpy2.rinterface_lib.conversion
               ._sexpcapsule_to_rinterface(obj.__sexp__))
    else:
        res = obj
    return res


def overlay_converter(src, target):
    """
    :param src: source of additional conversion rules
    :type src: :class:`Converter`
    :param target: target. The conversion rules in the src will
                   be added to this object.
    :type target: :class:`Converter`
    """
    for k, v in src.py2rpy.registry.items():
        # skip the root dispatch
        if k is object and v is _py2rpy:
            continue
        target._py2rpy.register(k, v)
    for k, v in src.rpy2py.registry.items():
        # skip the root dispatch
        if k is object and v is _rpy2py:
            continue
        target._rpy2py.register(k, v)
    target._rpy2py_nc_map = src._rpy2py_nc_map.copy()


def _py2rpy(obj):
    """ Dummy function for py2rpy.

    This function will convert Python objects into rpy2.rinterface
    objects.
    """
    raise NotImplementedError(
        "Conversion 'py2rpy' not defined for objects of type '%s'" %
        str(type(obj))
    )


def _rpy2py(obj):
    """ Dummy function for rpy2py.

    This function will convert Python objects into Python (presumably
    non-rpy2) objects.
    """
    raise NotImplementedError(
        "Conversion 'rpy2py' not defined for objects of type '%s'" %
        str(type(obj))
    )


class Converter(object):
    """
    Conversion between rpy2's low-level and high-level proxy objects
    for R objects, and Python (no R) objects.

    Converter objects can be added, the result being
    a Converter objects combining the translation rules from the
    different converters.
    """
    name = property(lambda self: self._name)
    py2rpy = property(lambda self: self._py2rpy)
    rpy2py = property(lambda self: self._rpy2py)
    rpy2py_nc_name = property(lambda self: self._rpy2py_nc_map)
    lineage = property(lambda self: self._lineage)

    def __init__(self, name,
                 template=None):
        (py2rpy, rpy2py) = Converter.make_dispatch_functions()
        self._name = name
        self._py2rpy = py2rpy
        self._rpy2py = rpy2py

        if template is None:
            lineage = tuple()
            self._rpy2py_nc_map = {}
        else:
            lineage = list(template.lineage)
            lineage.append(name)
            lineage = tuple(lineage)
            overlay_converter(template, self)
        self._lineage = lineage

    def __add__(self, converter):
        assert isinstance(converter, Converter)
        new_name = '%s + %s' % (self.name, converter.name)
        # create a copy of `self` as the result converter
        result_converter = Converter(new_name, template=self)
        overlay_converter(converter, result_converter)
        return result_converter

    @staticmethod
    def make_dispatch_functions():
        py2rpy = singledispatch(_py2rpy)
        rpy2py = singledispatch(_rpy2py)
        return (py2rpy, rpy2py)

    def rclass_map_context(self, cls, d: dict):
        return NameClassMapContext(
            self._rpy2py_nc_map[cls],
            d)


class ConversionContext(object):
    """
    Context manager for instances of class Converter.
    """
    def __init__(self, ctx_converter):
        assert isinstance(ctx_converter, Converter)
        self._original_converter = converter
        self.ctx_converter = Converter('Converter-%i-in-context' % id(self),
                                       template=ctx_converter)

    def __enter__(self):
        set_conversion(self.ctx_converter)
        return self.ctx_converter

    def __exit__(self, exc_type, exc_val, exc_tb):
        set_conversion(self._original_converter)
        return False


localconverter = ConversionContext

converter = None
py2rpy = None
rpy2py = None


def set_conversion(this_converter):
    """
    Set conversion rules in the conversion module.
    :param this_converter: The conversion rules
    :type this_converter: :class:`Converter`
    """
    global converter, py2rpy, rpy2py
    converter = this_converter
    py2rpy = converter.py2rpy
    rpy2py = converter.rpy2py


set_conversion(Converter('base converter'))
