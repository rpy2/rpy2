***********
rpy_classic
***********

The module aims at providing an API similar to
the one in RPy-1.x.

Loading the module can be done as:

>>> from rpy2.rpy_classic import *


The conversion system is still around:

>>> set_default_mode(NO_CONVERSION)
>>> set_default_mode(BASIC_CONVERSION)

The ``r`` instance behaves like before:

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

Functions
---------

As in RPy-1.x, all R objects are callable:

>>> callable(r.seq)
True
>>> callable(r.pi)
True
>>>

>>> r.seq(1, 3)
>>> r.seq(1, 3, by=0.5)
>>> r['options'](show_coef_Pvalues=0)

Whenever object is not a function, a runtime error
is thrown by R.

>>> r.pi()

  


>>> m = r.matrix(r.rnorm(100), 20, 5)
>>> pca = r.princomp(m)
>>> r.plot(pca, main = "PCA")

