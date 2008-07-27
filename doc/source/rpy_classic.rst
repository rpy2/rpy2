
***********
rpy_classic
***********

.. module:: rpy2.rpy_classic
   :platform: Unix, Windows
   :synopsis: Emulate the orignal rpy


This module provides an API similar to the one 
in RPy-1.x (*rpy*).

To match examples and documentation for *rpy*,
we load the module as:

>>> from rpy2.rpy_classic import *

.. index::
   single: conversion
   single: rpy_classic; conversion

Conversion
==========

Although the proposed high-level interface in :mod:`rpy2.robjects`
does not need explicit conversion settings, the conversion system 
existing in *rpy* is provided, and the default
mode can be set with :func:`set_default_mode`:

>>> set_default_mode(NO_CONVERSION)
>>> set_default_mode(BASIC_CONVERSION)

R instance
==========

The ``r`` instance of class :class:`R` behaves like before:

>>> r.help

'dots' in the R name are translated to underscores:

>>> r.wilcox_test

>>> r.wilcox_test([1,2,3], [4,5,6])

>>> x = r.seq(1, 3, by=0.5)
>>> r.plot(x)

An example::

  degrees = 4
  grid = r.seq(0, 10, length=100)
  values = [r.dchisq(x, degrees) for x in grid]
  r.par(ann=0)
  r.plot(grid, values, type='l')

  r.library('splines')

  type(r.seq)

.. index::
   pair: rpy_classic;function

Functions
=========

As in RPy-1.x, all R objects are callable:

>>> callable(r.seq)
True
>>> callable(r.pi)
True
>>>

If an object is not a R function, a :class:`RuntimeError`
is thrown by R whenever called:

>>> r.pi()

The function are called like regular Python functions:

>>> r.seq(1, 3)
>>> r.seq(1, 3, by=0.5)
>>> r['options'](show_coef_Pvalues=0)
>>>


  


>>> m = r.matrix(r.rnorm(100), 20, 5)
>>> pca = r.princomp(m)
>>> r.plot(pca, main = "PCA")
>>>
