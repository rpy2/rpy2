.. module:: rpy2.robjects.conversion
   :synopsis: Shuttling between low-level and higher(er)-level representations

.. _robjects-conversion:

Mapping rpy2 objects to arbitrary python objects
=====================================================

Switching between a conversion and a no conversion mode,
an operation often present when working with RPy-1.x, is no longer
necessary with `rpy2`.

The approach followed in `rpy2` has 2 levels, and conversion functions
help moving between them.

:mod:`rpy.rinterface`
---------------------

Protocols
^^^^^^^^^

At the lower level (:mod:`rpy2.rinterface`), the Python objects exposing
R objects implement Python protocols to make them feel as natural to a Python
programmer as possible. For example, R vectors are mapped
to Python objects implementing the :meth:`__getitem__` method in the sequence
protocol so elements can be accessed easily, R function are mapped to Python
objects implementing the :meth:`__call__` so they can be called just as if
they were functions.

This is implemented at the C level in `rpy` and there is no easy way to
customize the way it is done.

.. note::

   :mod:`rpy2`-exposed R vector implement the Python buffer protocol, and
   aim at making as much use of it as possible, but at the time of writing
   its adoption in other modules remains disappointingly limited.


:func:`ri2ro`
^^^^^^^^^^^^^

At this level the conversion is between lower-level (:mod:`rpy2.rinterface`)
objects and higher-level objects. By default this conversion method returns
:mod:`rpy2.robjects` objects, but can be customized to return instances
of arbitrary classes. For example the :mod:`numpy` optional converter
will return numpy arrays whenever possible.


:mod:`rpy2.robjects`
--------------------


.. note::

   `robjects`-level objects are also implicitly `rinterface`-level objects
   because of the inheritance relationship in their class definition,
   but the reverse is not true.
   The `robjects` level is an higher level of abstraction, aiming at simplifying
   one's use of R from Python (even if at the cost of performances). See Section
   XXX for more details.



Customizing the conversion
--------------------------

As an example, let's assume that one want to return atomic values
whenever an R numerical vector is of length one. This is only a matter
of writing a new function `ri2py` that handles this, as shown below:

.. code-block:: python

   import rpy2.robjects as robjects

   def my_ri2ro(obj):
       res = robjects.default_ri2ro(obj)
       if isinstance(res, robjects.Vector) and (len(res) == 1):
           res = res[0]
       return res

   robjects.conversion.ri2ro = my_ri2ro

Then we can test it with:

>>> pi = robjects.r.pi
>>> type(pi)
<type 'float'>

The default behavior can be restored with:

>>> robjects.conversion.ri2ro = default_ri2ro

Default functions
-----------------

The docstrings for :meth:`default_ri2ro`, :meth:`default_py2ri`, 
and :meth:`py2ro` are:

.. autofunction:: rpy2.robjects.default_ri2ro
.. .. autofunction:: rpy2.robjects.default_py2ri
.. .. autofunction:: rpy2.robjects.default_py2ro


