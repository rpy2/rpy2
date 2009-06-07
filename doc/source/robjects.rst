


********************
The robjects package
********************

.. module:: rpy2.robjects
   :platform: Unix, Windows
   :synopsis: High-level interface with R


Overview
========

This module should be the right pick for casual and general use.
Its aim is to abstract some of the details and provide an
intuitive interface to both Python and R programmers.


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

Being a singleton means that each time the constructor
for :class:`R` is called the same instance is returned;
this is required by the fact that the embedded R is stateful.

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

That last limitation can partly be removed by using :mod:`rpy2.rpy_classic` if
this feature matters most to you.

>>> robjects.r.as_null
# AttributeError raised
>>> import rpy2.rpy_classic as rpy
>>> rpy.set_default_mode(NO_CONVERSION)
>>> rpy.r.as_null
# R function as.null() returned

.. note::

   The section :ref:`rpy_classic-mix` outlines how to integrate
   :mod:`rpy2.rpy_classic` code.


Behind the scene, the steps for getting an attribute of `r` are
rather straightforward:
 
  1. Check if the attribute is defined as such in the python definition for
     `r`

  2. Check if the attribute is can be accessed in R, starting from `globalenv`

When safety matters most, we recommend using :meth:`__getitem__` to get
a given R object.

>>> as_null = robjects.r['as.null']

Storing the object in a python variable will protect it from garbage
collection, even if deleted from the objects visible to an R user.

>>> robjects.globalenv['foo'] = 1.2
>>> foo = robjects.r['foo']
>>> foo[0]
1.2

Here we `remove` the symbol `foo` from the R Global Environment.

>>> robjects.r['rm']('foo')
>>> robjects.r['foo']
LookupError: 'foo' not found

The object itself remains available, and protected from R's
garbage collection until `foo` is deleted from Python

>>> foo[0]
1.2


Evaluating a string as R code
-----------------------------

Just like it is the case with RPy-1.x, on-the-fly
evaluation of R code contained in a string can be performed
by calling the `r` instance:

>>> print(robjects.r('1+2'))
[1] 3
>>> sqr = robjects.r('function(x) x^2')

>>> print(sqr)
function (x)
x^2
>>> print(sqr(2))
[1] 4

The astute reader will quickly realize that R objects named
by python variables can
be plugged into code through their `R` representation:

>>> x = robjects.r.rnorm(100)
>>> robjects.r('hist(%s, xlab="x", main="hist(x)")' %x.r_repr())

.. warning::

   Doing this with large objects might not be the best use of
   your computing power.

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


.. autoclass:: rpy2.robjects.RVector(o)
   :show-inheritance:
   :members:


Creating vectors
----------------

Creating vectors can be achieved either from R or from Python.

When the vectors are created from R, one should not worry much
as they will be exposed as they should by :mod:`rpy2.robjects`.

When one wants to create a vector from Python, either the 
class :class:`RVector` or the convenience classes
:class:`IntVector`, :class:`FloatVector`, :class:`BoolVector`, 
:class:`StrVector` can be used.

.. autoclass:: rpy2.robjects.vectors.BoolVector(obj)
   :show-inheritance:
   :members:

.. autoclass:: rpy2.robjects.vectors.IntVector(obj)
   :show-inheritance:
   :members:

.. autoclass:: rpy2.robjects.vectors.FloatVector(obj)
   :show-inheritance:
   :members:

.. autoclass:: rpy2.robjects.vectors.StrVector(obj)
   :show-inheritance:
   :members:

FactorVector
^^^^^^^^^^^^

R's factors are somewhat peculiar: they aim at representing
a memory-efficient vector of labels, and in order to achieve it
are implemented as vectors of integers, to which are associated a (presumably
shorter) vector of labels. Each integer represents the position
of the label in the associated vector of labels.


>>> sv = ro.StrVector('ababbc')
>>> fac = ro.FactorVector(sv)
>>> print(fac)
[1] a b a b b c
Levels: a b c
>>> tuple(fac)
(1, 2, 1, 2, 2, 3)
>>> tuple(fac.levels)
('a', 'b', 'c')

When extracting elements from a :class:`FactorVector`, a sensible default
might be to use R-style extracting (see :ref:`robjects-extracting`) 

.. autoclass:: rpy2.robjects.vectors.FactorVector(obj)
   :show-inheritance:
   :members:


.. index::
   pair: RVector;extracting

.. _robjects-extracting:

Extracting items
----------------

Extracting elements of sequence/vector can become a thorny issue
as Python and R differ on a number of points
(index numbers starting at zero / starting at one,
negative index number meaning *index from the end* / *everything except*,
names cannot / can be used for subsettting).

In order to solve this, the Python way and the R way were
made available through two different routes.

Extractiong, Python-style
^^^^^^^^^^^^^^^^^^^^^^^^^

The python :meth:`__getitem__` method behaves like a Python user would expect
it for a vector (and indexing starts at zero).

>>> x = robjects.r.seq(1, 5)
>>> tuple(x)
(1, 2, 3, 4, 5)
>>> x.names = robjects.StrVector('abcde')
>>> print(x)
a b c d e 
1 2 3 4 5
>>> x[0]
1
>>> x[4]
5
>>> x[-1]
5

Extracting, R-style
^^^^^^^^^^^^^^^^^^^

Access to R-style extracting/subsetting is granted though the two
delegators *rx* and *rx2*, representing the R function *[* and *[[*
respectively.

In short, R-style extracting has the following characteristics:

* indexing starts at one

* the parameter to subset on can be a vector of 

  - integers (negative integers meaning exlusion of the elements)

  - booleans

  - strings (whenever the vector has *names* for its elements)


>>> print(x.rx(1))
[1] 1
>>> print(x.rx(robjects.IntVector((1, 3))))
[1] 1 3

R/S have particularities, in which some see consistency issues.
For example although the indexing starts at 1, indexing on 0
does not return an *index out of bounds* error but a vector
of length 0:

>>> print(x.rx(0))
integer(0)

The two next examples demonstrate some of `R`'s features
(such as element exclusion and the recycling rule):

>>> print(x.rx(-1))
2:5
>>> print(x.rx(robjects.IntVector((-1, -3))))
[1] 2 4 5
>>> print(x.rx(True))
1:5
>>> print(x.rx(robjects.BoolVector((False, True, False, True, True))))
[1] 2 4 5
>>> print(x.rx('a'))
a
1

Operators
---------

Mathematical operations on two vectors: the following operations
are performed element-wise in R, recycling the shortest vector if, and
as much as, necessary.

The delegating attribute mentioned in the Indexing section can also
be used with the following operators:

+----------+----------+
| operator | R (.ro)  |
+==========+==========+
| ``+``    | Add      |
+----------+----------+
| ``-``    | Subtract |
+----------+----------+
| ``*``    | Multiply |
+----------+----------+
| ``/``    | Divide   |
+----------+----------+
| ``**``   | Power    |
+----------+----------+
| ``or``   | Or       |
+----------+----------+
| ``and``  | And      |
+----------+----------+

>>> x = robjects.r.seq(1, 10)
>>> print(x.ro + 1)
2:11

.. note::
   In Python, the operator ``+`` concatenates sequence objects, 
   and this behavior has been conserved.

.. note::
   The boolean operator ``not`` cannot be redefined in Python (at least up to
   version 2.5), and its behavior could not be made to mimic R's behavior

.. index::
   single: names; robjects

Names
-----

``R`` vectors can have a name given to all or some of the elements.
The property :attr:`names` can be used to get, or set, those names.

>>> x = robjects.r.seq(1, 5)
>>> x.names = robjects.StrVector('abcde')
>>> x.names[0]
'a'
>>> x.names[0] = 'z'
>>> tuple(x.names)
('z', 'b', 'c', 'd', 'e')


.. index::
   pair: robjects;REnvironment
   pair: robjects;globalenv

:class:`RArray`
---------------

In `R`, arrays are simply vectors with a dimension attribute. That fact
was reflected in the class hierarchy with :class:`robjects.RArray` inheriting
from :class:`robjects.RVector`.

.. autoclass:: rpy2.robjects.vectors.RArray(obj)
   :show-inheritance:
   :members:



:class:`RMatrix`
----------------

A :class:`RMatrix` is a special case of :class:`RArray`.

>>> m = robjects.r.matrix(robjects.IntVector(range(10)), nrow=5)
>>> print(m)
     [,1] [,2]
[1,]    0    5
[2,]    1    6
[3,]    2    7
[4,]    3    8
[5,]    4    9

.. autoclass:: rpy2.robjects.vectors.RMatrix(obj)
   :show-inheritance:
   :members:



Extracting
^^^^^^^^^^

Extracting can still be performed Python-style or
R-style.


>>> m[0]
0
>>> m[5]
5
>>> print(m.rx(1))
[1] 0
>>> print(m.rx(6))
[1] 5

Matrixes are two-dimensional arrays, and elements can
be extracted according to two indexes:

>>> print(m.rx(1,1))
[1] 0
>>> print(m.rx(3,2))
[1] 7


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

Creating objects
^^^^^^^^^^^^^^^^

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


>>> import rpy2.rlike.container as rlc
>>> od = rlc.OrdDict(c(('value', robjects.IntVector((1,2,3))),
                       ('letter', robjects.StrVector(('x', 'y', 'z')))))
>>> dataf = robjects.RDataFrame(od)
>>> print(dataf.colnames)
[1] "letter" "value"

.. note::
   The order of the columns `value` and `letter` cannot be conserved,
   since we are using a Python dictionnary. This difference between
   R and Python can be resolved by using TaggedList instances
   (XXX add material about that).

Extracting elements
^^^^^^^^^^^^^^^^^^^

Here again, Python's :meth:`__getitem__` will work
as a Python programmer will expect it to:

>>> len(dataf)
2
>>> dataf[0]
<RVector - Python:0x8a58c2c / R:0x8e7dd08>

The :class:`RDataFrame` is composed of columns,
with each column being possibly of a different type:

>>> [column.rclass[0] for column in dataf]
['factor', 'integer']

Using R-style access to elements is a little more richer,
with the *rx2* accessor taking now more importance than earlier.

Like with Python's :meth:`__getitem__` above,
extracting on one index selects columns:

>>> dataf.rx(1)
<RDataFrame - Python:0x8a584ac / R:0x95a6fb8>
>>> print(dataf.rx(1))
  letter
1      x
2      y
3      z

It is important to notice that the result is itself
of class :class:`RDataFrame`. Getting the column as
a vector is requires the use of *rx2*.

>>> dataf.rx2(1)
<RVector - Python:0x8a4bfcc / R:0x8e7dd08>
>>> print(dataf.rx2(1))
[1] x y z
Levels: x y z


Since data frames are table-like structure, they
can be thought of as two-dimensional arrays and
can therefore be extracted on two indexes.

>>> subdataf = dataf.rx(1, True)
>>> print(subdataf)
  letter value
1      x     1
>>> subdataf = dataf.rx(robjects.IntVector((1,3)), True)
>>> print(subdataf)
  letter value
1      x     1
3      z     3


Python docstrings
^^^^^^^^^^^^^^^^^

.. autoclass:: rpy2.robjects.vectors.RDataFrame(tlist)
   :show-inheritance:
   :members:


.. _robjects-environments:

Environments
============

R environments can be described to the Python user as
an hybrid of a dictionary and a scope.

The first of all environments is called the Global Environment,
that can also be referred to as the R workspace.

An R environment in RPy2 can be seen as a kind of Python
dictionnary.

Assigning a value to a symbol in an environment has been
made as simple as assigning a value to a key in a Python
dictionary:

>>> robjects.r.ls(globalenv)
>>> globalEnv["a"] = 123
>>> print(robjects.r.ls(globalenv))


Care must be taken when assigning objects into an environment
such as the Global Environment, as this can hide other objects
with an identical name.
The following example should make one measure that this can mean
trouble if no care is taken:

>>> globalenv["pi"] = 123
>>> print(robjects.r.pi)
[1] 123
>>>
>>> robjects.r.rm("pi")
>>> print(robjects.r.pi)
[1] 3.1415926535897931

The class inherits from the class
:class:`rpy2.rinterface.SexpEnvironment`.


An environment is also iter-able, returning all the symbols
(keys) it contains:

>>> env = robjects.r.baseenv()
>>> len([x for x in env])
<a long list returned>

.. autoclass:: rpy2.robjects.REnvironment(o=None)
   :show-inheritance:
   :members:



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

This is all looking fine and simple until R parameters with names 
such as `na.rm` are encountered. In those cases, using the special
syntax `**kwargs` is one way to go.

Let's take an example in R:

.. code-block:: r

   sum(0, na.rm = TRUE)

In Python it can then write:

.. code-block:: python

   from rpy2 import robjects

   myparams = {'na.rm': True}
   robjects.r.sum(0, **myparams)

Things are also not always that simple, as the use of a dictionary does
not ensure that the order in which the parameters are passed is conserved.

The R functions as defined in :mod:`rpy2.robjects` inherit from the class
:class:`rpy2.rinterface.SexpClosure`, and further documentation
on the behavior of function can be found in Section :ref:`rinterface-functions`.

.. autoclass:: rpy2.robjects.RFunction(*args, **kwargs)
   :show-inheritance:
   :members:


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
  env = fmla.environment
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

  fit = robjects.r('lm(%s)' %fmla.r_repr())

.. autoclass:: rpy2.robjects.RFormula(formula, environment = rinterface.globalenv)
   :show-inheritance:
   :members:



Class diagram
=============

.. inheritance-diagram:: rpy2.robjects rpy2.robjects.methods rpy2.robjects.vectors
   :parts: 1



