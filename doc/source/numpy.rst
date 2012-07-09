

Numpy
=====

A popular solution for scientific computing with Python is :mod:`numpy` 
(previous instances were :mod:`Numpy` and :mod:`numarray`).

:mod:`rpy2` has features to ease bidirectional communication with :mod:`numpy`.

High-level interface
--------------------

From `rpy2` to `numpy`:
^^^^^^^^^^^^^^^^^^^^^^^

R vectors or arrays can be converted to :mod:`numpy` arrays using
:meth:`numpy.array` or :meth:`numpy.asarray`:

.. code-block:: python

   import numpy

   ltr = robjects.r.letters
   ltr_np = numpy.array(ltr)

This behavior is inherited from the low-level interface;
vector-like objects inheriting from :class:`rpy2.rinterface.SexpVector`
present an interface recognized by `numpy`.


.. code-block:: python

   from rpy2.robjects.packages import importr
   import numpy

   datasets = importr('datasets')
   ostatus = datasets.occupationalStatus
   ostatus_np = numpy.array(ostatus)
   ostatus_npnc = numpy.asarray(ostatus)

The matrix *ostatus* is an 8x8 matrix:

>>> print(ostatus)
      destination
origin   1   2   3   4   5   6   7   8
     1  50  19  26   8   7  11   6   2
     2  16  40  34  18  11  20   8   3
     3  12  35  65  66  35  88  23  21
     4  11  20  58 110  40 183  64  32
     5   2   8  12  23  25  46  28  12
     6  12  28 102 162  90 554 230 177
     7   0   6  19  40  21 158 143  71
     8   0   3  14  32  15 126  91 106

Its content has been copied to a numpy array:

>>> ostatus_np
array([[ 50,  19,  26,   8,   7,  11,   6,   2],
       [ 16,  40,  34,  18,  11,  20,   8,   3],
       [ 12,  35,  65,  66,  35,  88,  23,  21],
       [ 11,  20,  58, 110,  40, 183,  64,  32],
       [  2,   8,  12,  23,  25,  46,  28,  12],
       [ 12,  28, 102, 162,  90, 554, 230, 177],
       [  0,   6,  19,  40,  21, 158, 143,  71],
       [  0,   3,  14,  32,  15, 126,  91, 106]])
>>> ostatus_np[0, 0]
50
>>> ostatus_np[0, 0] = 123
>>> ostatus_np[0, 0]
123
>>> ostatus.rx(1, 1)[0]
50

On the other hand, *ostatus_npnc* is a view on *ostatus*; no copy was made:

>>> ostatus_npnc[0, 0] = 456
>>> ostatus.rx(1, 1)[0]
456

Since we did modify an actual R dataset for the session, we should restore it:

>>> ostatus_npnc[0, 0] = 50

As we see, :meth:`numpy.asarray`: provides a way to build a *view* on the underlying
R array, without making a copy. This will be of particular appeal to developpers whishing
to mix :mod:`rpy2` and :mod:`numpy` code, with the :mod:`rpy2` objects or the :mod:`numpy` view passed to
functions, or for interactive users much more familiar with the :mod:`numpy` syntax.


.. note::

   The current interface is relying on the *__array_struct__* defined
   in numpy.
   
   Python buffers, as defined in :pep:`3118`, is the way to the future,
   and rpy2 is already offering them... although as a (poorly documented)
   experimental feature.

From `numpy` to `rpy2`:
^^^^^^^^^^^^^^^^^^^^^^^

The conversion of `numpy` objects to `rpy2` objects can be 
activated by importing the module :mod:`numpy2ri`::

  from rpy2.robjects.numpy2ri import numpy2ri
  ro.conversion.py2ri = numpy2ri

This is sufficient to switch an automatic conversion
of `numpy` objects into `rpy2` objects.

.. warning::

   In earlier versions of rpy2, the import was all that was needed to
   have the conversion. A side-effect when importing a module can
   lead to problems, and there is now an extra step to make the
   conversion active: call the function :func:`rpy2.robjects.activate`.

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
be used to construct `numpy` arrays:


>>> import numpy
>>> rx = rinterface.SexpVector([1,2,3,4], rinterface.INTSXP)
>>> nx = numpy.array(rx)
>>> nx_nc = numpy.asarray(rx)


.. note::
   when using :meth:`numpy.asarray`, the data are not copied.

>>> rx[2]
3
>>> nx_nc[2] = 42
>>> rx[2]
42
>>>

