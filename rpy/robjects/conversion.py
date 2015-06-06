"""
The module contains the conversion functions to be
used by the rpy2.robjects functions and methods.

These functions are initially empty place-holders,
raising a NotImplementedError exception.
"""

import sys
from collections import namedtuple

if sys.version_info[0] < 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 4):
    from singledispatch import singledispatch
else:
    from functools import singledispatch

Converter = namedtuple('Converter', 'name ri2ro py2ri py2ro ri2py lineage')

def make_converter(name, template=None):
    """ Create a converter. `template` is an optional converter to use as base converter,
    that is the `class -> function` associations will be copied in the new converter. """

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

    @singledispatch
    def ri2py(obj):
        """ Dummy function for ri2py.

        This function will convert Python objects into Python (presumably non-rpy2) objects.
        """
        raise NotImplementedError("Conversion 'ri2py' not defined for objects of type '%s'" % str(type(obj)))

    if template is not None:
        lineage = list(template.lineage)
        lineage.append(name)
        lineage = tuple(lineage)
        for k,v in template.ri2ro.registry.items():
            ri2ro.register(k, v)
        for k,v in template.py2ri.registry.items():
            py2ri.register(k, v)
        for k,v in template.py2ro.registry.items():
            py2ro.register(k, v)
        for k,v in template.ri2py.registry.items():
            ri2py.register(k, v)
    else:
        lineage = tuple()
    return Converter(name, ri2ro, py2ri, py2ro, ri2py, lineage)

converter = make_converter('base converter')
converter_name, py2ri, ri2ro, py2ro, ri2py, converter_lineage = converter
