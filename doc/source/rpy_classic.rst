
***********
rpy_classic
***********

.. module:: rpy2.rpy_classic
   :synopsis: Emulate the orignal rpy


This module provides an API *similar* to the one 
in RPy-1.x (*rpy*).

.. warning::

   The implementation of the RPy-1.x characteristics is incomplete.
   This is likely not due to limitations in the low-level interface
   :mod:`rpy2.rinterface` but due to limited time from this author,
   and from limited contributions to get it improved.

To match examples and documentation for *rpy*,
we load the module as:

>>> import rpy2.rpy_classic as rpy

.. index::
   single: conversion
   single: rpy_classic; conversion

Conversion
==========

Although the proposed high-level interface in :mod:`rpy2.robjects`
does not need explicit conversion settings, the conversion system 
existing in *rpy* is provided, and the default
mode can be set with :func:`set_default_mode`:

>>> rpy.set_default_mode(rpy.NO_CONVERSION)
>>> rpy.set_default_mode(rpy.BASIC_CONVERSION)

R instance
==========

The ``r`` instance of class :class:`R` behaves like before:

>>> rpy.r.help

'dots' in the R name are translated to underscores:

>>> rpy.r.wilcox_test

>>> rpy.r.wilcox_test([1,2,3], [4,5,6])

>>> x = rpy.r.seq(1, 3, by=0.5)
>>> rpy.r.plot(x)

An example::

  degrees = 4
  grid = rpy.r.seq(0, 10, length=100)
  values = [rpy.r.dchisq(x, degrees) for x in grid]
  rpy.r.par(ann=0)
  rpy.r.plot(grid, values, type='l')

  rpy.r.library('splines')

  type(rpy.r.seq)

.. index::
   pair: rpy_classic;function

Functions
=========

As in RPy-1.x, all R objects are callable:

>>> callable(rpy.r.seq)
True
>>> callable(rpy.r.pi)
True
>>>

If an object is not a R function, a :class:`RuntimeError`
is thrown by R whenever called:

>>> rpy.r.pi()

The function are called like regular Python functions:

>>> rpy.r.seq(1, 3)
>>> rpy.r.seq(1, 3, by=0.5)
>>> rpy.r['options'](show_coef_Pvalues=0)
>>>


  


>>> m = rpy.r.matrix(r.rnorm(100), 20, 5)
>>> pca = rpy.r.princomp(m)
>>> rpy.r.plot(pca, main = "PCA")
>>>

.. _rpy_classic-mix:

Partial use of :mod:`rpy_classic`
==================================

The use of rpy_classic does not need to be
exclusive of the other interface(s) proposed
in rpy2.

Chaining code designed for either of the interfaces
is rather easy and, among other possible use-cases,
should make the inclusion of legacy rpy code into newly
written rpy2 code a simple take.

The link between :mod:`rpy_classic` and the rest
of :mod:`rpy2` is the property :attr:`RObj.sexp`,
that give the representation of the underlying R object
in the low-level :mod:`rpy2.rinterface` definition.
This representation can then be used in function calls
with :mod:`rpy2.rinterface` and :mod:`rpy2.robjects`.
With :mod:`rpy2.robjects`, a conversion using 
:func:`rpy2.robjects.default_ri2py` can be considered.

.. note::

   Obviously, that property `sexp` is not part of the original
   `Robj` in rpy.


An example:

.. code-block:: python

   import rpy2.robjects as ro
   import rpy2.rpy_classic as rpy
   rpy.set_default_mode(rpy.NO_CONVERSION)


   def legacy_paste(v):
       # legacy rpy code
       res = rpy.r.paste(v, collapse = '-')
       return res


   rletters = ro.r['letters']

   # the legaxy code is called using an rpy2.robjects object
   alphabet_rpy = legacy_paste(rletters)

   # convert the resulting rpy2.rpy_classic object to
   # an rpy2.robjects object
   alphabet = ro.default_ri2py(alphabet_rpy.sexp)
