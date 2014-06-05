Overview
========

This module should be the right pick for casual and general use.
Its aim is to abstract some of the details and provide an
intuitive interface to both Python and R programmers.


>>> import rpy2.robjects as robjects

:mod:`rpy2.robjects` is written on top of :mod:`rpy2.rinterface`, and one
not satisfied with it could easily build one's own flavor of a
Python-R interface by modifying it (:mod:`rpy2.rpy_classic` is another
example of a Python interface built on top of :mod:`rpy2.rinterface`).

Visible differences with RPy-1.x are:

- no ``CONVERSION`` mode in :mod:`rpy2`, the design has made this unnecessary

- easy to modify or rewrite with an all-Python implementation
