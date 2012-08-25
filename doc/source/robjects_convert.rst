.. module:: rpy2.robjects.conversion
   :synopsis: Shuttling between low-level and higher(er)-level representations

.. _robjects-conversion:

Mapping rpy2 objects to arbitrary python objects
=====================================================

Switching between a conversion and a no conversion mode,
an operation often present when working with RPy-1.x, is no longer
necessary with rpy2.

The approach of rpy2 is to have R-wrapping objects that implement
interfaces of builtin Python types whenever possible, letting the
Python layer access the objects the usual way and the wrapped R objects be
used as they are by the R functions. For example, R vectors are mapped
to Python objects implementing the :meth:`__getitem__` method in the sequence
protocol, so elements can be accessed easily.

There is a low-level mapping between `R` and `Python` objects
performed behind the (Python-level) scene, done at the :mod:`rpy2.rinterface` level,
while a higher-level mapping is done between low-level objects and
higher-level objects. The later is performed by the functions:

:meth:`conversion.ri2py`
   :mod:`rpy2.rinterface` to Python. By default, this function
   is just an alias for the function :meth:`default_ri2py`.

:meth:`conversion.py2ri`
   Python to :mod:`rpy2.rinterface`. By default, this function
   is just an alias for the function :meth:`default_py2ri`.

:meth:`conversion.py2ro`
   Python to :mod:`rpy2.robjects`. By default, that one function
   is merely a call to :meth:`conversion.py2ri` 
   followed by a call to :meth:`conversion.ri2py`.

Those functions can be redefined to suits one's need.
The easiest option is to write a custom function calling
the default function when the custom conversion should not apply.

A simple example
----------------

As an example, let's assume that one want to return atomic values
whenever an R numerical vector is of length one. This is only a matter
of writing a new function `ri2py` that handles this, as shown below:

.. code-block:: python

   import rpy2.robjects as robjects

   def my_ri2py(obj):
       res = robjects.default_ri2py(obj)
       if isinstance(res, robjects.Vector) and (len(res) == 1):
           res = res[0]
       return res

   robjects.conversion.ri2py = my_ri2py

Then we can test it with:

>>> pi = robjects.r.pi
>>> type(pi)
<type 'float'>

The default behavior can be restored with:

>>> robjects.conversion.ri2py = default_ri2py

Default functions
-----------------

The docstrings for :meth:`default_ri2py`, :meth:`default_py2ri`, 
and :meth:`py2ro` are:

.. autofunction:: rpy2.robjects.default_ri2py
.. autofunction:: rpy2.robjects.default_py2ri
.. autofunction:: rpy2.robjects.default_py2ro


