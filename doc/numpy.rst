.. _robjects-numpy:

Numpy
=====

A popular solution for scientific computing with Python is :mod:`numpy`.

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

   from rpy2.robjects.packages import importr, data
   import numpy

   datasets = importr('datasets')
   ostatus = data(datasets).fetch('occupationalStatus')['occupationalStatus']
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

Some of the conversions operations require the copy of data in R structures
into Python structures. Whenever this happens, the time it takes and the
memory required will depend on object sizes. Because of this reason the
use of a local converter is recommended: it makes limiting the use
of conversion rules to code blocks of interest easier to achieve.

.. code-block:: python
   
   from rpy2.robjects import numpy2ri
   from rpy2.robjects import default_converter

   # Create a converter that starts with rpy2's default converter
   # to which the numpy conversion rules are added.
   np_cv_rules = default_converter + numpy2ri.converter

   with np_cv_rules:
       # Anything here and until the `with` block is exited
       # will use our numpy converter whenever objects are
       # passed to R or are returned by R while calling
       # rpy2.robjects functions.
       pass

An example of usage is:

.. code-block:: python

   from rpy2.robjects.packages import importr
   stats = importr('base')
   with np_cv_rules.context():
       v_np = stats.rlogis(100, location=0, scale=1)
       # `v_np` is a numpy array

   # Outside of the scope of the local converter the
   # result will not be automatically converted to a
   # numpy object.
   v_nonp = stats.rlogis(100, location=0, scale=1)

.. note::

   Why make :mod:`numpy` an optional feature for :mod:`rpy2`?
   This was a design decision taken in order to:
   - ensure that :mod:`rpy2` can function without :mod:`numpy`. An early motivation for
   this was compatibility with Python 3 and dropping support for Python 2.
   :mod:`rpy2` did that much earlier than :mod:`numpy` did.
   - make potentially resource-consuming conversions optional

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

