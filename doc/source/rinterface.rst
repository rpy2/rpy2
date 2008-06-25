.. index::
   module: rpy2.rinterface

**********
rinterface
**********

.. module:: rpy2.rinterface
   :synopsis: Low-level interface with R


Overview
========

A lower-level interface is provided for cases where
the use-cases addressed by :mod:`robjects` are not covered,
and for the cases where the layer in :mod:`robjects`
has an excessive cost in term of performances.

The package can be imported with:

>>> import rpy2.rinterface as rinterface

.. index::
   single: initEmbeddedR
   single: initialize

:func:`initEmbeddedR`
---------------------

One has to initialize R before much can be done.
The function :func:`initEmbeddedR` lets one initialize
the embedded R:

>>> rinterface.initEmbeddedR()

Initialization should only be performed once and in the case
of a second call to :func:`initEmbeddedR`, to avoid unpredictable results
when using the embedded R, an exception is be fired.

Parameters for the initialization are in the module variable
`initOptions`.

.. index::
   single: initialize R_HOME

.. note::
   If calling :func:`initEmbeddedR` returns an error stating that
   `R_HOME` is not defined, you should either have the R executable in
   your path (`$PATH` on unix-alikes, `%Path%` on Microsoft Windows) or
   have the environment variable `R_HOME` defined. 

R space and Python space
------------------------

When using the RPy2 package, two realms are co-existing: R and Python.

The :class:`Sexp_Type` objects can be considered as Python enveloppes pointing
to data stored and administered in the R space.

.. index::
   single: globalEnv
   single: SexpEnvironment; globalEnv

globalEnv
---------

The global environment can be seen as the root (or topmost) environment,
and is in fact a list, that is a sequence, of environments.

When an R library (package in R's terminology) is loaded,
is it added to the existing sequence of environments. Unless
specified, it is inserted in second position. The first position
always remains attributed to the global environment
(FIXME: there is a bit of circulariry in this definition - check
how to present it a clear(er) way).
The library is said to be attached to the current search path.

.. index::
   pair: rinterface; baseNamespaceEnv
   single: SexpEnvironment; baseNamespaceEnv

baseNamespaceEnv
----------------

The base package has a namespace, that can be accessed as an environment.

.. note::
   Depending on what is in `globalEnv` and on the attached packages, base
   objects can be masked when starting the search from `globalEnv`. Use this
   environment when you want to be sure to access a function you know to be
   in the base namespace.

.. index::
   single: Sexp

:class:`Sexp`
=============

Methods:


typeof()
    Type of the object

do_slot([name])
    Access attribute *name* for the object

.. index::
   single: Sexp; typeof

:meth:`typeof`
--------------

The internal R type in which an object is stored can be
accessed with the method :meth:`typeof`.

>>> letters.typeof()

FIXME: talk about the all the types.

.. index::
   single: Sexp; do_slot

:meth:`do_slot`
---------------

R objects can be given attributes. In R the function
*attr* lets one access attribute, while called :meth:`do_slot`
in the C interface to R. 


>>> matrix = rinterface.globalEnv.get("matrix")
>>> letters = rinterface.globalEnv.get("letters")
>>> ncol = rinterface.SexpVector([2, ], rinterface.INTSXP)
>>> m = matrix(letters, ncol = ncol)
>>> [x for x in m.do_slot("dim")]
[13, 2]
>>>

.. index::
   single: SexpVector
   single: rinterface; SexpVector

:class:`SexpVector`
===================

Overview
--------

In R all scalars are in fact vectors.
Anything like a one-value variable is a vector of
length 1.

To use again the constant *pi*:

>>> pi = rinterface.globalEnv.get("pi")
>>> len(pi)
1
>>> pi
<rinterface.SexpVector - Python:0x2b20325d2660 / R:0x16d5248>
>>> pi[0]
3.1415926535897931
>>>

The letters of the (western) alphabet are:

>>> letters = rinterface.globalEnv.get("letters") 
>>> len(letters)
26
>>> LETTERS = rinterface.globalEnv.get("LETTERS") 


.. index::
   pair: rinterface;indexing

Indexing
--------

The indexing is working like it would on regular `Python`
tuples or lists.
The indexing starts at 0 (zero), which differs from `R`, 
where indexing start at 1 (one).

.. note::
   The *__getitem__* operator *[*
   is returning a Python scalar. Casting
   an *SexpVector* into a list is only a matter 
   either iterating through it, or simply calling
   the constructor :func:`list`.


Common attributes
-----------------

.. index::
   single: names

Names
^^^^^

In R, vectors can be named, that is each value in the vector
can be given a name (that is be associated a string).
The names are added to the other as an attribute (conveniently
called `names`), and can be accessed as such:

>>> options = rinterface.globalEnv.get("options")()
>>> option_names = options.do_slot("names")
>>> [x for x in options_names]

.. note::
   Elements in a vector of names do not have to be unique.

.. index::
   single: dim
   single: dimnames


Dim and dimnames
^^^^^^^^^^^^^^^^

In the case of an `array`, the names across the
respective dimensions of the object are accessible
through the slot named `dimnames`.



.. index::
   pair: SexpVector; numpy

Numpy
-----

The :class:`SexpVector` objects are made to behave like arrays as defined
in the Python package :mod:`numpy`.

The functions *array* and *asarray* is all that is needed:

>>> import numpy
>>> rx = rinterface.SexpVector([1,2,3,4], rinterface.INTSXP)
>>> nx = numpy.array(rx)
>>> nx_nc = numpy.asarray(rx)


.. note::
   when using :meth:`asarray`, the data are not copied.

>>> nx_nc[2] = 42
>>> rx[2]
42
>>>

.. index::
   single: SexpEnvironment
   single: rinterface; SexpEnvironment

:class:`SexpEnvironment`
========================

:meth:`get`
-----------

Whenever a search for a symbol is performed, the whole
search path is considered: the environments in the list
are inspected in sequence and the value for the first symbol found
matching is returned.

>>> rinterface.globalEnv.get("pi")

The constant pi is defined in the package base, that
is by default in the search path.

FIXME: get functions only


:meth:`__getitem__` / :meth:`__setitem__`
-----------------------------------------

The *[* operator will only look for a symbol in the environment
(FIXME: first in the list then ?),
without looking into other elements in the list.

The following will return an exception :class:`LookupError`:

>>> rinterface.globalEnv["pi"]

The constant *pi* is defined in R's *base* package,
and therefore cannot be found in the Global Environment.

The assignment of a value to a symbol in an environment is as
simple as assigning a value to a key in a Python dictionary:

>>> x = rinterface.Sexp_Vector([123, ], rinterface.INTSXP)
>>> rinterface.globalEnv["x"] = x

note: a copy of the R object is made in the R space.

:meth:`__iter__`
----------------

The object is made iter-able.

For example, we take the base name space (that is the environment
that contains R's base objects:

>>> base = rinterface.baseNameSpace
>>> basetypes = [x.typeof() for x in base]


Note that in the current implementation the content of the environment
is evaluated only once, when the iterator is created, and that adding 
or removing elements to the environment after will not have any effect.

.. index::
   single: closure
   single: SexpClosure
   single: rinterface; SexpClosure
   pair: rinterface; function

:class:`SexpClosure`
====================

A function with a context
-------------------------

In R terminology, a closure is a function (with its enclosing
environment). That enclosing environment can be thought of as
a context to the function.

>>> sum = rinterface.globalEnv.get("sum")
>>> x = rinterface.SexpVector([1,2,3], rinterface.INTSXP)
>>> s = sum(x)
>>> s[0]
6
>>>

closureEnv
----------

In the example below, we inspect the environment for the
function *plot*, that is the namespace for the
package *graphics*.

>>> plot = rinterface.globalEnv.get("plot")
>>> ls = rinterface.globalEnv.get("ls")
>>> envplot_list = ls(plot.closureEnv())
>>> [x for x in envplot_ls]
>>>





Misc. variables
===============

.. index::
   single: R_LEN_T_MAX
   single: R_HOME
   single: TRUE
   single: FALSE


R_HOME
  R HOME

:const:`R_LEN_T_MAX`
  largest usable integer for indexing R vectors

:const:`TRUE`/:const:`FALSE`
  R's TRUE and FALSE

.. index::
   single: missing values

Missing values
--------------

:const:`NA_INTEGER`
  Missing value for integers

:const:`NA_LOGICAL`
  Missing value for booleans

:const:`NA_REAL`
  Missing value for numerical values (float / double)

.. index::
   single: ENVSXP
   single: type; ENVSXP
   single: INTSXP
   single: type; INTSXP
   single: LGLSXP
   single: type; LGLSXP
   single: STRSXP
   single: type; STRSXP
   single: REALSXP
   single: type; REALSXP

R types
-------

:const:`INTSXP`
  Integer

:const:`REALSXP`
  Numerical value (float / double)

:const:`LGLSXP`
  Boolean (logical in the R terminology)

:const:`STRSXP`
  String

:const:`ENVSXP`
  Environment

:const:`CPLXSXP`
  Complex 

