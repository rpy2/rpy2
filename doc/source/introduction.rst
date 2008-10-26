********************
Introduction to rpy2
********************


This introduction aims at being a gentle start to rpy2,
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

If familiar with R and the R console, :data:`r` is a little like your window
to R from Python.


The method :meth:`__getitem__` functions like calling a variable from the
R console.

Example in R:

.. code-block:: r

   pi

With :mod:`rpy2`:

>>> robjects.r['pi']
3.14159265358979



The :data:`r` object is also callable, and the string passed to it evaluated
as `R` code:

Example in R:

.. code-block:: r

   pi

With :mod:`rpy2`:

>>> robjects.r('pi')
3.14159265358979


The evaluation is performed in what is know to R users as the 
`Global Environment`, that is the place one starts at when starting
the R console. Whenever the `R` code creates variables, those
variables will be "located" in that `Global Environment` by default.


Example:

.. code-block:: r

   robjects.r('''
	   f <- function(r) { 2 * pi * r }
           f(3)
	   ''')


The expression above will return the value 18.85, but also create an R function
`f`. That function `f` is present in the R `Global Environement`, and can
be accessed with the `__getitem__` mechanism outlined above:


>>> robjects.r['f']
function (r) 
{
    2 * pi * r
}


R vectors
=========

In `R`, data are mostly represented by vectors, even when looking
like scalars.

When looking closely at the R object `pi` used previously,
we can observe that this is in fact a vector of length 1.

>>> len(robjects.r['pi'])
1


Creating R vectors can be achieved simply:

>>> robjects.StrVector(['abc', 'def'])
c("abc", "def")
>>> robjects.IntVector([1, 2, 3])
1:3
>>> robjects.FloatVector([1.1, 2.2, 3.3])
c(1.1, 2.2, 3.3)


R matrixes and arrays are just vector with a `dim` attribute.


 