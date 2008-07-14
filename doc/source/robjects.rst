
*************
rpy2.robjects
*************

.. module:: rpy2.robjects
   :platform: Unix, Windows
   :synopsis: High-level interface with R

.. testsetup:: robjects
   import rpy2.robjects as robjects

Overview
========

This module is intended for casual and general use.
Its aim is to abstracts some of the details and provide an
intuitive interface to R.


>>> import rpy2.robjects as robjects


:mod:`rpy2.robjects` is written on the top of :mod:`rpy2.rinterface`, and one
not satisfied with it could easily build one's own flavor of a
Python-R interface by modifying it (:mod:`rpy2.rpy_classic` is an other
example of a Python interface built on the top of :mod:`rpy2.rinterface`).

Visible differences with RPy-1.x are:

- no CONVERSION mode in :mod:`rpy2`, the design has made this unnecessary

- easy to modify or rewrite with an all-Python implementation



`r`: the instance of `R`
==============================

This class is currently a singleton, with
its one representation instanciated when the
module is loaded:


>>> robjects.r
>>> print(robjects.r)

The instance can be seen as the entry point to an
embedded R process, and the elements that would be accessible
from an equivalent R environment are accessible as attributes
of the instance.
Readers familiar with the :mod:`ctypes` module for Python will note
the similarity with it.

R vectors:

>>> pi = robjects.r.pi
>>> letters = robjects.r.letters


R functions:

>>> plot = robjects.r.plot
>>> dir = robjects.r.dir


Strings as R code
-----------------

Just like it is the case with RPy-1.x, on-the-fly
evaluation of R code contained in a string can be performed
by calling the `r` instance:

>>> robjects.r('1+2')
3
>>> sqr = ro.r('function(x) x^2)

>>> sqr
function (x)
x^2
>>> sqr(2)
4

The astute reader will quickly realize that R objects named
by python variables can
be plugged into code through their string representation:

>>> x = robjects.r.rnorm(100)
>>> robjects.r('hist(%s, xlab="x", main="hist(x)")' %repr(x))



.. index::
   pair: robjects;RObject

R objects
=========

The class :class:`rpy2.robjects.RObject`
represents an arbitray R object, meaning than object
cannot be represented by any of the classes :class:`RVector`,
:class:`RFunction`, :class:`REnvironment`. 

The class inherits from the class
:class:`rpy2.rinterface.Sexp`.

.. index::
   pair: robjects;RVector

R vectors
=========

Beside functions, and environemnts, most of the objects
an R user is interacting with are vector-like.
For example, this means that any scalar is in fact a vector
of length one.

The class :class:`RVector` has a constructor:

>>> x = robjects.RVector(3)

The class inherits from the class
:class:`rpy2.rinterface.VectorSexp`.


.. index::
   pair: RVector;indexing

Indexing
--------

Indexing can become a thorny issue, since Python indexing starts at zero
and R indexing starts at one.

The python :meth:`__getitem__` method behaves like a Python user would expect
it for a vector (and indexing starts at zero),
while the method :meth:`subset` behaves like a R user would expect it
(indexing starts at one, and a vector of integers, booleans, or strings can
be given to subset elements).

>>> x = robjects.r.seq(1, 10)
>>> x[0]
1
>>> x.subset(0)
integer(0)
>>> x.subset(1)
1L

Rather than calling :meth:`subset`, and to still have the conveniently
short `[` operator available, a syntactic sugar is available in
the form of delegating-like attribute :attr:`r`.

>>> x.r[0]
integer(0)
>>> x.r[1]
1L

The two next examples demonstrate some of `R`'s features regarding indexing,
respectively element exclusion and recycling rule:

>>> x.r[-1]
2:10
>>> x.r[True]
1:10

This class is using the class :class:`rinterface.SexpVector`, 
and its documentation can be referred to for details of what is happenening
at the low-level.

Operators
---------

Mathematical operations on two vectors: the following operations
are performed element-wise in R, recycling the shortest vector if, and
as much as, necessary.

The delegating attribute mentioned in the Indexing section can also
be used with the following operators:

+----------+---------+
| operator | R (.r)  |
+----------+---------+
| ``+``    | Add     |
+----------+---------+
| ``-``    | Subtract|
+----------+---------+
| ``*``    | Multiply|
+----------+---------+
| ``/``    | Divide  |
+----------+---------+
| ``**``   | Power   |
+----------+---------+
| ``or``   | Or      |
+----------+---------+
| ``and``  | And     |
+----------+---------+

>>> x = robjects.r.seq(1, 10)
>>> x.r + 1
2:11

.. index::
   pair: RVector; numpy

Numpy
-----

Vectors can be converted to :mod:`numpy` arrays using
:meth:`array` or :meth:`asarray`::

  import numpy
  ltr = robjects.r.letters
  ltr_np = numpy.array(ltr)

Refer to the documentation for :class:`rinterface.SexpVector`
for further details.

.. index::
   pair: robjects;REnvironment
   pair: robjects;globalEnv

:class:`RArray`
---------------

In `R`, arrays are simply vectors with a dimension attribute. That fact
was reflected in the class hierarchy with :class:`robjects.RArray` inheriting
from :class:`robjects.RVector`.

:class:`RMatrix`
----------------

A :class:`RMatrix` is a special case of :class:`RArray`.


:class:`RDataFrame`
-------------------

A :class:`RDataFrame` represents the `R` class `data.frame`.

Currently, the constructor is flagged as experimental. It accepts either a :class:`rinterface.SexpVector`
or a dictonnary which elements will be the columns of the `data.frame`.

R environments
==============

R environments can be described to the Python user as
an hybrid of a dictionary and a scope.

The first of all environments is called the Global Environment,
that can also be referred to as the R workspace.

>>> globalEnv = robjects.globalEnv


An R environment in RPy2 can be seen as a kind of Python
dictionnary.

Assigning a value to a symbol in an environment has been
made as simple as assigning a value to a key in a Python
dictionary:

>>> robjects.r.ls(globalEnv)
>>> globalEnv["a"] = 123
>>> robjects.r.ls(globalEnv)


Care must be taken when assigning objects into an environment
such as the Global Environment, as this can hide other objects
with an identical name.
The following example should make one measure that this can mean
trouble if no care is taken:

>>> globalEnv["pi"] = 123
>>> robjects.r.pi
123L
>>>
>>> robjects.r.rm("pi")
>>> robjects.r.pi
3.1415926535897931

The class inherits from the class
:class:`rpy2.rinterface.SexpEnvironment`.


An environment is also iter-able, returning all the symbols
(keys) it contains:

>>> env = robjects.r.baseenv()
>>> len([x for x in env])

.. index::
   pair: robjects; RFunction
   pair: robjects; function

R functions
===========

>>> plot = robjects.r.plot
>>> rnorm = robjects.r.rnorm
>>> plot(rnorm(100), ylab="random")


The class inherits from the class
:class:`rpy2.rinterface.SexpClosure`.

.. index::
   pair: robjects; RFormula
   single: formula

Formulae
========

For tasks such as modelling and plotting, an R formula can be
a terse, yet readable, way of expressing what is wanted.

In R, it generally looks like:

.. code-block:: r

  x <- 1:10
  y <- x + rnorm(10, sd=0.2)

  fit <- lm(y ~ x) 

In the call to `lm`, the argument is a `formula`.
A formula is a `R` language object, and the terms in the formula
are evaluated in the environment it was defined in. Without further
specification, that environment is the environment in which the
the formula is created.

The class :class:`robjects.RFormula` is representing an `R` formula.

.. code-block:: python

  x = robjects.RVector(array.array('i', range(1, 11)))
  y = x.r + robjects.r.rnorm(10, sd=0.2)

  fmla = robjects.RFormula('y ~ x')
  env = fmla.getenvironment()
  env['x'] = x
  env['y'] = y

  fit = robjects.r.lm(fmla)

One drawback with that approach is that pretty printing of
the `fit` object is note quite as clear as what one would
expect when working in `R`.
However, by evaluating R code on
the fly, we can obtain a `fit` object that will display
nicely:

.. code-block:: python

  fit = robjects.r('lm(%s)' %repr(fmla))


Mapping between rpy2 objects and other python objects
=====================================================

The conversion, often present when working with RPy-1.x, is no longer
necessary as the R objects can be either passed on to R functions
or used in Python. 

However, there is a low-level mapping between `R` and `Python` objects
performed behind the (Python-level) scene, done by the :mod:`rpy2.rinterface`,
while an higher-level mapping is done between low-level objects and
higher-level objects using the functions:

:meth:`ri2py`
   :mod:`rpy2.rinterface` to Python. By default, this function
   is just an alias for the function :meth:`default_ri2py`.

:meth:`py2ri`
   Python to :mod:`rpy2.rinterface`. By default, this function
   is just an alias for the function :meth:`default_py2ri`.

:meth:`py2ro`
   Python to :mod:`rpy2.robjects`. That one function
   is merely a call to :meth:`py2ri` followed by a call to :meth:`ri2py`.

Those functions can be modifyied to satisfy all requirements, with
the easiest option being to write a custom function calling itself
the default function.
As an example, let's assume that one want to return atomic values
whenever an R numerical vector is of length one. This is only a matter
of writing a new function `ri2py` that handles this, as shown below:

.. code-block:: python

   import rpy2.robjects as robjects

   def my_ri2py(obj):
       res = robjects.default_ri2py(obj)
       if isinstance(res, robjects.RVector) and (len(res) == 1):
           res = res[0]
       return res

   robjects.ri2py = my_ri2py

Once this is done, we can verify immediately that this is working with:

>>> pi = robjects.r.pi
>>  type(pi)
<type 'float'>
>>> 


Examples
========

The following section demonstrates some of the features of
rpy2 by the example. The wiki on the sourceforge website
will hopefully be used as a cookbook.


.. code-block:: python

  import rpy2.robjects as robjects
  import array

  r = robjects.r

  x = array.array('i', range(10))
  y = r.rnorm(10)

  r.X11()

  r.layout(r.matrix(array.array('i', [1,2,3,2]), nrow=2, ncol=2))
  r.plot(r.runif(10), y, xlab="runif", ylab="foo/bar", col="red")

  kwargs = {'ylab':"foo/bar", 'type':"b", 'col':"blue", 'log':"x"}
  r.plot(x, y, **kwargs)

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
   import array

   r = robjects.r

   ctl = array.array('f', [4.17,5.58,5.18,6.11,4.50,4.61,5.17,4.53,5.33,5.14])
   trt = array.array('f', [4.81,4.17,4.41,3.59,5.87,3.83,6.03,4.89,4.32,4.69])
   group = r.gl(2, 10, 20, labels = ["Ctl","Trt"])
   weight = ctl + trt

   robjects.globalEnv["weight"] = weight
   robjects.globalEnv["group"] = group
   lm_D9 = r.lm("weight ~ group")
   print(r.anova(lm_D9))

   lm_D90 = r.lm("weight ~ group - 1")
   print(r.summary(lm_D90))

   

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
   


S4 classes
----------

.. code-block:: python

   import rpy2.robjects as robjects
   import array

   r = robjects.r

   r.setClass("Track",
              r.representation(x="numeric", y="numeric"))

   a = r.new("Track", x=0, y=1)

   a.x