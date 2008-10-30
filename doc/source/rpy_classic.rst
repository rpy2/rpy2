
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
