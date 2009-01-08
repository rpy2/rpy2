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

.. note::

   Under the hood, the variable `pi` is gotten by default from the
   R *base* package, unless an other variable with the name `pi` was
   created in the `globalEnv`. The Section :ref:`robjects-environments`
   tells more about that.


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

>>> robjects.globalEnv['f']
function (r) 
{
    2 * pi * r
}

or 

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
>>> rcode = 'paste(%s, collapse="-")' %(letters.r_repr())
>>> res = robjects.r(rcode)
>>> print(res)
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

>>> res = robjects.StrVector(['abc', 'def'])
>>> print(res.r_repr())
c("abc", "def")
>>> res = robjects.IntVector([1, 2, 3])
>>> print(res.r_repr())
1:3
>>> res = robjects.FloatVector([1.1, 2.2, 3.3])
>>> print(res.r_repr())
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
>>> rsum(robjects.IntVector([1,2,3]))[0]
6L

Keywords can be used with the same ease:

>>> rsort = robjects.r['sort']
>>> res = rsort(robjects.IntVector([1,2,3]), decreasing=True)
>>> print(res.r_repr())
c(3L, 2L, 1L)


.. note::

   By default, calling R functions will return R objects.


More information on functions is in Section :ref:`robjects-functions`.


Examples
========

This section demonstrates some of the features of
rpy2 by the example.


Function calls and plotting
---------------------------

.. code-block:: python

  import rpy2.robjects as robjects

  r = robjects.r

  x = robjects.IntVector(range(10))
  y = r.rnorm(10)

  r.X11()

  r.layout(r.matrix(robjects.IntVector([1,2,3,2]), nrow=2, ncol=2))
  r.plot(r.runif(10), y, xlab="runif", ylab="foo/bar", col="red")

Setting dynamically the number of arguments in a function call can be
done the usual way in python

.. code-block:: python

  args = [x, y]
  kwargs = {'ylab':"foo/bar", 'type':"b", 'col':"blue", 'log':"x"}
  r.plot(*args, **kwargs)

.. note::
   Since the named parameters are a Python :class:`dict`, 
   the order of the parameters is lost for `**kwargs` arguments. 


Linear models
-------------

The R code is:

.. code-block:: r

   ctl <- c(4.17,5.58,5.18,6.11,4.50,4.61,5.17,4.53,5.33,5.14)
   trt <- c(4.81,4.17,4.41,3.59,5.87,3.83,6.03,4.89,4.32,4.69)
   group <- gl(2, 10, 20, labels = c("Ctl","Trt"))
   weight <- c(ctl, trt)

   anova(lm.D9 <- lm(weight ~ group))

   summary(lm.D90 <- lm(weight ~ group - 1))# omitting intercept

One way to achieve the same with :mod:`rpy2.robjects` is

.. code-block:: python

   import rpy2.robjects as robjects

   r = robjects.r

   ctl = robjects.FloatVector([4.17,5.58,5.18,6.11,4.50,4.61,5.17,4.53,5.33,5.14])
   trt = robjects.FloatVector([4.81,4.17,4.41,3.59,5.87,3.83,6.03,4.89,4.32,4.69])
   group = r.gl(2, 10, 20, labels = ["Ctl","Trt"])
   weight = ctl + trt

   robjects.globalEnv["weight"] = weight
   robjects.globalEnv["group"] = group
   lm_D9 = r.lm("weight ~ group")
   print(r.anova(lm_D9))

   lm_D90 = r.lm("weight ~ group - 1")
   print(r.summary(lm_D90))

Q:
   Now how extract data from the resulting objects ?

A:
   The same, never it is. On the R object all depends.

When taking the results from the code above, one could go like:

>>> print(lm_D9.rclass)
[1] "lm" 

Here the resulting object is a list structure, as either inspecting
the data structure or reading the R man pages for `lm` would tell us.
Checking its element names is then trivial:

>>> print(lm_D9.names)
 [1] "coefficients"  "residuals"     "effects"       "rank"         
 [5] "fitted.values" "assign"        "qr"            "df.residual"  
 [9] "contrasts"     "xlevels"       "call"          "terms"        
[13] "model" 

And so is extracting a particular element:

>>> print(lm_D9.r['coefficients'])
$coefficients
(Intercept)    groupTrt 
      5.032      -0.371 

More about extracting elements from vectors is available
at :ref:`robjects-vectors-indexing`.
   
Principal component analysis
----------------------------

The R code is

.. code-block:: r

  m <- matrix(rnorm(100), ncol=5)
  pca <- princomp(m)
  plot(pca, main="Eigen values")
  biplot(pca, main="biplot")

The :mod:`rpy2.robjects` code is

.. testcode::

  import rpy2.robjects as robjects

  r = robjects.r

  m = r.matrix(r.rnorm(100), ncol=5)
  pca = r.princomp(m)
  r.plot(pca, main="Eigen values")
  r.biplot(pca, main="biplot")
   



