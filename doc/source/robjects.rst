
********************
High-level interface
********************

.. module:: rpy2.robjects
   :platform: Unix, Windows
   :synopsis: High-level interface with R


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

- no ``CONVERSION`` mode in :mod:`rpy2`, the design has made this unnecessary

- easy to modify or rewrite with an all-Python implementation



`r`: the instance of `R`
========================

This class is currently a singleton, with
its one representation instanciated when the
module is loaded:


>>> robjects.r
>>> print(robjects.r)

The instance can be seen as the entry point to an
embedded R process.

The elements that would be accessible
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

This approach has limitation as:

  * The actual Python attributes for the object masks the R elements 

  * '.' (dot) is syntactically valid in names for R objects, but not for
    python objects.

That last limitation can partly be removed by setting the attribute
:attr:`_dotter` from False to True.

>>> robjects.r.as_null
# AttributeError raised
>>> robjects.r._dotter = True
>>> robjects.r.as_null
# R function as.null() returned

.. warning::
   In the case there are R objects which name only differ by '.' and '_'
   (e.g., 'my_variable' and 'my.variable'), setting :attr:`_dotter` to True
   can result in confusing results at runtime.

Behind the scene, the steps for getting an attribute of `r` are
rather straightforward:
 
  1. Check if the attribute is defined as such in the python definition for
     `r`

  2. Check if the attribute is can be accessed in R, starting from `globalEnv`

  3. If :attr:`_dotter` is True, turn all `_` into `.` and repeat the step above

When safety matters most, we recommed using :meth:`__getitem__` to get
and R object (and store it in a python variable if wanted):

>>> as_null = robjects.r['as.null']


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

.. _robjects-vectors:

Vectors
=======

Beside functions, and environemnts, most of the objects
an R user is interacting with are vector-like.
For example, this means that any scalar is in fact a vector
of length one.

The class :class:`RVector` has a constructor:

>>> x = robjects.RVector(3)

The class inherits from the class
:class:`rpy2.rinterface.VectorSexp`.


Creating vectors
----------------

Creating vectors can be achieved either from R or from Python.

When the vectors are created from R, one should not worry much
as they will be exposed as they should by :mod:`rpy2.robjects`.

When one wants to create a vector from Python, either the 
class :class:`RVector` or the convenience classes
:class:`IntVector`, :class:`FloatVector`, :class:`BoolVector`, :class:`StrVector` can
used.

.. autoclass:: rpy2.robjects.BoolVector
   :show-inheritance:
   :members:

.. autoclass:: rpy2.robjects.IntVector
   :show-inheritance:
   :members:

.. autoclass:: rpy2.robjects.FloatVector
   :show-inheritance:
   :members:

.. autoclass:: rpy2.robjects.StrVector
   :show-inheritance:
   :members:



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

.. note::
   In Python, the operator ``+`` concatenate sequence object, and this behavior
   has been conserved.

.. note::
   The boolean operator ``not`` cannot be redefined in Python (at least up to
   version 2.5), and its behavior could be made to mimic R's behavior

.. index::
   single: names; robjects

Names
-----

``R`` vectors can have a name given to all or some of the items.
The method :meth:`getnames` retrieve those names.


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


.. _robjects-dataframes:

Data frames
-----------


Data frames are important data structures in R, as they are used to
represent a data to analyze in a study in a relatively 
large nunmber of cases.

A data frame can be thought of as a tabular representation of data,
with one variable per column, and one data point per row. Each column
is an R vector, which implies one type for all elements
in one given column, and which allows for possibly different types across
different columns.


In :mod:`rpy2.robjects`, 
:class:`RDataFrame` represents the `R` class `data.frame`.

Creating an :class:`RDataFrame` can be done by:

* Using the constructor for the class

* Create the data.frame through R

The constructor for :class:`RDataFrame` accepts either a 
:class:`rinterface.SexpVector` 
(with :attr:`typeof` equal to *VECSXP*, that is an R `list`)
or an instance of class :class:`rpy2.rlike.container.TaggedList`.

>>> robjects.RDataFrame()


Creating the data.frame in R can be achieved in numerous ways,
as many R functions do return a data.frame.
In this example, will use the R function `data.frame()`, that
constructs a data.frame from named arguments

>>> d = {'value': robjects.IntVector((1,2,3)),
         'letter': robjects.StrVector(('x', 'y', 'z'))}
>>> dataf = robjects.r['data.frame'](**d)
>>> dataf.colnames()
c("letter", "value")

.. note::
   The order of the columns `value` and `letter` cannot be conserved,
   since we are using a Python dictionnary. This difference between
   R and Python can be resolved by using TaggedList instances
   (XXX add material about that).

.. autoclass:: rpy2.robjects.RDataFrame
   :show-inheritance:
   :members:


Environments
============

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
<a long list returned>

For further information, read the documentation for the
class :class:`rpy2.rinterface.SexpEnvironment`.

.. index::
   pair: robjects; RFunction
   pair: robjects; function

.. _robjects-functions:

Functions
=========

R functions are callable objects, and be called almost like any regular
Python function:

>>> plot = robjects.r.plot
>>> rnorm = robjects.r.rnorm
>>> plot(rnorm(100), ylab="random")

In Python, arguments to a function are split into two groups:

* A first group for which parameters are in defined order

* A second group for which parameters are associated a name/keyword,
  and a default value. In that second group the order is lost, as it is
  passed as a Python dictionary.

Those two groups can be used in function calls.


The class inherits from the class
:class:`rpy2.rinterface.SexpClosure`, and further documentation
on the behavior of function can be found in Section :ref:`rinterface-functions`.

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

In the call to `lm`, the argument is a `formula`, and it can read like
*model y using x*.
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


Mapping rpy2 objects to arbitrary python objects
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
>>>  type(pi)
<type 'float'>
>>> 

The default behavoir can be restored with:

>>> robjects.ri2py = default_ri2py

The docstrings for :meth:`default_ri2py`, :meth:`default_py2ri`, and :meth:`py2ro` are:

.. autofunction:: rpy2.robjects.default_ri2py
.. autofunction:: rpy2.robjects.default_py2ri
.. autofunction:: rpy2.robjects.default_py2ro


Examples
========

This section demonstrates some of the features of
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

.. note::
   Since the named parameters are a Python :class:`dict`, 
   the order of the parameters is lost. 
   Check :meth:`rpy2.rinterface.SexpClosure.rcall`
   to know how to keep the order of parameters.

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


