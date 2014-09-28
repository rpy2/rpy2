.. module:: rpy2.robjects.conversion
   :synopsis: Shuttling between low-level and higher(er)-level representations

.. _robjects-conversion:

Mapping rpy2 objects to arbitrary python objects
=====================================================

.. note::

   Switching between a conversion and a no conversion mode,
   an operation often present when working with RPy-1.x, is no longer
   necessary with `rpy2`.

   The approach followed in `rpy2` has 2 levels (`rinterface` and `robjects`),
   and conversion functions help moving between them.


Protocols
---------

At the lower level (:mod:`rpy2.rinterface`), the rpy2 objects exposing
R objects implement Python protocols to make them feel as natural to a Python
programmer as possible. With them they can be passed as arguments to many
non-rpy2 functions without the need for conversion.

R vectors are mapped to Python objects implementing the methods :meth:`__getitem__` / :meth:`__setitem__` in the sequence
protocol so elements can be accessed easily. They also implement the Python buffer protocol,
allowing them be used in :mod:`numpy` functions without the need for data copying or conversion.

R functions are mapped to Python
objects implementing the :meth:`__call__` so they can be called just as if
they were functions.

R environments are mapped to Python objects implementing :meth:`__getitem__` / :meth:`__setitem__` in the mapping
protocol so elements can be accessed similarly to in a Python :class:`dict`.

.. note::

   The `rinterface` level is largely implemented in C, bridging Python and R C-APIs.
   There is no easy way to customize it.


Conversion functions
--------------------

:func:`ri2ro`
^^^^^^^^^^^^^

At this level the conversion is between lower-level (:mod:`rpy2.rinterface`)
objects and higher-level (:mod:`rpy2.robjects`) objects.
This method is a generic as implemented in :meth:`functools.singledispatch`
(with Python 2, :meth:`singledispatch.singledispatch`).


:func:`ri2py`
^^^^^^^^^^^^^

At this level the conversion is between lower-level (:mod:`rpy2.rinterface`)
objects and any objects (presumably non-rpy2 is the conversion can be made).
This method is a generic as implemented in :meth:`functools.singledispatch`
(with Python 2, :meth:`singledispatch.singledispatch`).

For example the optional conversion scheme for :mod:`numpy` objects
will return numpy arrays whenever possible.


.. note::

   `robjects`-level objects are also implicitly `rinterface`-level objects
   because of the inheritance relationship in their class definition,
   but the reverse is not true.
   The `robjects` level is an higher level of abstraction, aiming at simplifying
   one's use of R from Python (although at the possible cost of performances).


:func:`p2ri`
^^^^^^^^^^^^^

At this level the conversion is between (presumably) non-rpy2 objects
and rpy2 lower-level (:mod:`rpy2.rinterface`).

This method is a generic as implemented in :meth:`functools.singledispatch`
(with Python 2, :meth:`singledispatch.singledispatch`).


Customizing the conversion
--------------------------

As an example, let's assume that one want to return atomic values
whenever an R numerical vector is of length one. This is only a matter
of writing a new function `ri2py` that handles this, as shown below:

.. code-block:: python

   import rpy2.robjects as robjects
   from rpy2.rinterface import SexpVector
   
   @robjects.conversion.ri2ro.register(SexpVector)
   def my_ri2ro(obj):
       if len(obj) == 1:
           obj = obj[0]
       return obj

Then we can test it with:

>>> pi = robjects.r.pi
>>> type(pi)
<type 'float'>

At the time of writing :func:`singledispath` does not provide a way to `unregister`.
Removing the additional conversion rule without restarting Python is left as an
exercise for the reader.

.. warning::

   The example is bending a little the rpy2 rules, as it is using `ri2ro` while it does not
   return an `robjects` instance when an R vector of length one. We are getting away with it
   because atomic Python types such as :class:`int`, :class:`float`, :class:`bool`, :class:`complex`,
   :class:`str` are well handled by rpy2 at the `rinterface`/C level.
