"""
The module contains the conversion functions to be
used by the rpy2.robjects functions and methods.

These functions are initially empty place-holders,
raising a NotImplementedError exception.
"""

import sys
from collections import namedtuple

if sys.version_info[0] < 3:
    from singledispatch import singledispatch
else:
    from functools import singledispatch

Converter = namedtuple('Converter', 'ri2ro py2ri py2ro')

def make_converter(template=None):
    """ Create a converter. Parent is an optional converter to use as a parent. """

    @singledispatch
    def ri2ro(obj):
        """ Dummy function for ri2ro.

        This function will convert rpy2.rinterface (ri) low-level objects
        into rpy2.robjects (ro) higher-level objects.
        """
        raise NotImplementedError("Conversion 'ri2ro' not defined for objects of type '%s'" % str(type(obj)))

    @singledispatch
    def py2ri(obj):
        """ Dummy function for py2ri.

        This function will convert Python objects into rpy2.rinterface
        (ri) objects.
        """
        raise NotImplementedError("Conversion 'py2ri' not defined for objects of type '%s'" % str(type(obj)))

    @singledispatch
    def py2ro(obj):
        """ Dummy function for py2ro.

        This function will convert Python objects into rpy2.robjects
        (ro) objects.
        """
        raise NotImplementedError("Conversion 'py2ro' not defined for objects of type '%s'" % str(type(obj)))

    if template is not None:
        for k,v in template.ri2ro.registry.items():
            ri2ro.register(k, v)
        for k,v in template.py2ri.registry.items():
            py2ri.register(k, v)
        for k,v in template.py2ro.registry.items():
            py2ro.register(k, v)

    return Converter(ri2ro, py2ri, py2ro)

converter = make_converter()
ri2ro, py2ri, py2ro = converter
