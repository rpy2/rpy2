
Numpy
=====

A popular solution for scientific computing with Python is :mod:`numpy` 
(previous instances were :mod:`Numpy` and :mod:`numarray`).

:mod:`rpy2` has features for facilitating the integration with code using
:mod:`numpy` in both directions: from `rpy2` to `numpy`, and from `numpy`
to `rpy2`.

High-level interface
--------------------

From `rpy2` to `numpy`:
^^^^^^^^^^^^^^^^^^^^^^^

Vectors can be converted to :mod:`numpy` arrays using
:meth:`array` or :meth:`asarray`::

  import numpy

  ltr = robjects.r.letters
  ltr_np = numpy.array(ltr)

This behavior is inherited from the low-level interface,
and is means that the objects presents an interface recognized by
`numpy`, and that interface used to know the structure of the object.



From `numpy` to `rpy2`:
^^^^^^^^^^^^^^^^^^^^^^^

The conversion of `numpy` objects to `rpy2` objects can be 
activated by importing the module :mod:`numpy2ri`::

  import rpy2.robjects.numpy2ri

That import alone is sufficient to switch an automatic conversion
of `numpy` objects into `rpy2` objects.


.. note::

   Why make this an optional import, while it could have been included
   in the function :func:`py2ri` (as done in the original patch 
   submitted for that function) ?

   Although both are valid and reasonable options, the design decision
   was taken in order to decouple `rpy2` from `numpy` the most, and
   do not assume that having `numpy` installed automatically
   meant that a programmer wanted to use it. 

.. note::

   The module :mod:`numpy2ri` is an example of how custom conversion to
   and from :mod:`rpy2.robjects` can be performed.

Low-level interface
-------------------

The :class:`rpy2.rinterface.SexpVector` objects are made to 
behave like arrays, as defined in the Python package :mod:`numpy`.

The functions :func:`numpy.array` and :func:`numpy.asarray` can
be used construct `numpy` arrays:


>>> import numpy
>>> rx = rinterface.SexpVector([1,2,3,4], rinterface.INTSXP)
>>> nx = numpy.array(rx)
>>> nx_nc = numpy.asarray(rx)


.. note::
   when using :meth:`asarray`, the data are not copied.

>>> rx[2]
3
>>> nx_nc[2] = 42
>>> rx[2]
42
>>>

