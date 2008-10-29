********************
Introduction to rpy2
********************


This introduction aims at making a gentle start to rpy2,
either when coming from R to Python/rpy2, from Python to rpy2/R,
or from elsewhere to Python/rpy2/R.


Getting started
===============

It is assumed here that the rpy2 package was properly installed.
In python, making a package or module available is achieved by
importing it.

.. code-block:: python

   import rpy2.robjects as robjects


The `r` instance
================

The object :data:`r` in :mod:`rpy2.robjects` represents the running embedded
`R` process.

If familiar with R and the R console, :data:`r` is a little like a
communication channel from Python to R.


Getting R objects
-----------------

In Python the `[` operator is an alias for the  ethod :meth:`__getitem__`.

With :mod:`rpy2.robjects`, 
the method :meth:`__getitem__` functions like calling a variable from the
R console.

Example in R:

.. code-block:: r

   pi

With :mod:`rpy2`:

>>> robjects.r['pi']
3.14159265358979



Evaluating R code
-----------------

The :data:`r` object is also callable, and the string passed to it evaluated
as `R` code.

This can be used to `get` variables, and provide an alternative to
the method presented above.

Example in R:

.. code-block:: r

   pi

With :mod:`rpy2`:

>>> robjects.r('pi')
3.14159265358979


.. warning::

   The result is an R vector. Reading Section
   :ref:`introduction-vectors` is recommended as it will provide explanations
   for the following behavior:
   
   >>> robjects.r('pi') + 2
   c(3.14159265358979, 2)
   >>> robjects.r('pi')[0] + 2
   5.1415926535897931


The evaluation is performed in what is known to R users as the 
`Global Environment`, that is the place one starts at when starting
the R console. Whenever the `R` code creates variables, those
variables will be "located" in that `Global Environment` by default.


Example:

.. code-block:: r

   robjects.r('''
	   f <- function(r) { 2 * pi * r }
           f(3)
	   ''')


The expression above will return the value 18.85, 
but first also creates an R function
`f`. That function `f` is present in the R `Global Environement`, and can
be accessed with the `__getitem__` mechanism outlined above:


>>> robjects.r['f']
function (r) 
{
    2 * pi * r
}

Interpolating R objects into R code strings
-------------------------------------------

Against the first impression one may get from the title
of this section, simple and handy features of :mod:`rpy2` are
presented here.

An R object has a string representation that can be used
directly into R code to be evaluated.

Simple example:

>>> letters = robjects.r['letters']
>>> rcode = 'paste(%s, collapse="-")' %(repr(letters))
>>> robjects.r(rcode)
"a-b-c-d-e-f-g-h-i-j-k-l-m-n-o-p-q-r-s-t-u-v-w-x-y-z"


.. _introduction-vectors:

R vectors
=========

In `R`, data are mostly represented by vectors, even when looking
like scalars.

When looking closely at the R object `pi` used previously,
we can observe that this is in fact a vector of length 1.

>>> len(robjects.r['pi'])
1

As such, the python method :meth:`add` will result in a concatenation
(function `c()` in R), as this is the case for regular python lists.

Accessing the one value in that vector will have to be stated
explicitly:

>>> robjects.r['pi'][0]
3.1415926535897931

There much that can be achieved with vector, having them to behave
more like Python lists or R vectors.
A comprehensive description of the behavior of vectors is found in
:ref:`robjects-vectors`.

Creating rpy2 vectors
---------------------

Creating R vectors can be achieved simply:

>>> robjects.StrVector(['abc', 'def'])
c("abc", "def")
>>> robjects.IntVector([1, 2, 3])
1:3
>>> robjects.FloatVector([1.1, 2.2, 3.3])
c(1.1, 2.2, 3.3)


R matrixes and arrays are just vectors with a `dim` attribute.

The easiest way to create such objects is to do it through
R functions:

>>> v = robjects.FloatVector([1.1, 2.2, 3.3, 4.4, 5.5, 6.6])
>>> m = robjects.r['matrix'](v, nrow = 2)
>>> print(m)
     [,1] [,2] [,3]
[1,]  1.1  3.3  5.5
[2,]  2.2  4.4  6.6


Calling R functions
===================

Calling R functions will be disappointingly similar to calling
Python functions:

>>> rsum = robjects.r['sum']
>>> rsum(robjects.IntVector([1,2,3]))
6L

Keywords can be used with the same ease:

>>> rsort = robjects.r['sort']
>>> rsort(robjects.IntVector([1,2,3]), decreasing=True)
c(3L, 2L, 1L)


.. note::

   By default, calling R functions will return R objects.


More information on functions is in Section :ref:`robjects-functions`
