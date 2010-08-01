


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
Python-R interface by modifying it (:mod:`rpy2.rpy_classic` is another
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


R objects
=========

The class :class:`rpy2.robjects.RObject`
can represent any arbitray R object, although it will often
be used for objects without any more specific representation
in Python/rpy2 (such as :class:`Vector`,
:class:`functions.Function`, :class:`Environment`).

The class inherits from the lower-level
:class:`rpy2.rinterface.Sexp`
and from :class:`rpy2.robjects.robject.RObjectMixin`, the later defining
higher-level methods for R objects to be shared by other higher-level
representations of R objects.

.. autoclass:: rpy2.robjects.robject.RObjectMixin
   :show-inheritance:
   :members:

.. autoclass:: rpy2.robjects.RObject
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
>>> robjects.globalenv["a"] = 123
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
>>> [x for x in env]
<a long list returned>

.. note:: 

   Although there is a natural link between environment
   and R packages, one should consider using the convenience wrapper
   dedicated to model R packages (see :ref:`robjects-packages`).
   

.. autoclass:: rpy2.robjects.Environment(o=None)
   :show-inheritance:
   :members:



.. index::
   pair: robjects; Function
   pair: robjects; function

.. _robjects-functions:

Functions
=========

R functions are callable objects, and be called almost like any regular
Python function:

>>> plot = robjects.r.plot
>>> rnorm = robjects.r.rnorm
>>> plot(rnorm(100), ylab="random")

This is all looking fine and simple until R arguments with names 
such as `na.rm` are encountered. By default, this is addressed by
having a translation of '.' (dot) in the R argument name into a '_' in the Python
argument name.

Let's take an example in R:

.. code-block:: r

   rank(0, na.last = TRUE)

In Python it can then write:

.. code-block:: python

   from rpy2.robjects.packages import importr
   base = importr('base')

   base.rank(0, na_last = True)

.. note::

   The object base.rank is an instance of
   :class:`functions.SignatureTranslatedFunction`,
   a child class of :class:`functions.Function`, and the translation of 
   the argument names made during
   the creation of the instance.
   This saves the need to translate the names at each function
   call, and allow to perform sanity check regarding possible 
   ambiguous translation with an acceptable cost (since this is 
   only performed when the instance is created).

   If translation is not desired, the class :class:`functions.Function` 
   can be used. With
   that class, using the special Python syntax `**kwargs` is one way to specify
   named arguments that contain a dot '.'

   It is important to understand that the translation is done by inspecting
   the signature of the R function, and that not much can be guessed from the
   R ellipsis '...' whenever present. Arguments falling in the '...' will need
   to have their R names passes, as show in the example below:

   >>> graphics = importr('graphics')
   >>> graphics.par(cex_axis = 0.5)
   Warning message:
   In function (..., no.readonly = FALSE)  :
   "cex_axis" is not a graphical parameter
   <Vector - Python:0xa1688cc / R:0xab763b0>
   >>> graphics.par(**{'cex.axis': 0.5})
   <Vector - Python:0xae8fbec / R:0xaafb850>

   There exists a way to specify manually a argument mapping:

   .. code-block:: python

      from rpy2.robjects.functions import SignatureTranslatedFunction
      from rpy2.robjects.packages import importr
      graphics = importr('graphics')
      graphics.par = SignatureTranslatedFunction(graphics.par,
                                                 init_prm_translate = {'cex_axis': 'cex.axis'})

   >>> graphics.par(cex_axis = 0.5)
   <Vector - Python:0xa2cc90c / R:0xa5f7fd8>

   Translating blindly each '.' in argument names into '_' currently appears
   to be a risky
   practice, and is left to one to decide for his own code. (Bad) example:
 
   .. code-block:: python

      def iamfeelinglucky(**kwargs):
          res = {}
          for k, v in kwargs.iteritems:
              res[k.replace('_', '.')] = v
          return res

      graphics.par(**(iamfeelinglucky(cex_axis = 0.5)))

    
   
Things are also not always that simple, as the use of a dictionary does
not ensure that the order in which the arguments are passed is conserved.

R is capable of introspection, and can return the arguments accepted
by a function through the function `formals()`, modelled as a method of
:class:`functions.Function`.

>>> from rpy2.robjects.packages import importr
>>> stats = importr('stats')
>>> rnorm = stats.rnorm
>>> rnorm.formals()
<Vector - Python:0x8790bcc / R:0x93db250>
>>> tuple(rnorm.formals().names)
('n', 'mean', 'sd')


.. warning::

   Here again there is a twist coming from R, and some functions are "special".
   rpy2 is exposing as :class:`rpy2.rinterface.SexpClosure`  R objects that 
   can be either CLOSXP, BUILTINSXP, or SPECIALSXP. However, only CLOSXP objects
   will return non-null `formals`.


The R functions as defined in :mod:`rpy2.robjects` inherit from the class
:class:`rpy2.rinterface.SexpClosure`, and further documentation
on the behavior of function can be found in Section :ref:`rinterface-functions`.

.. autoclass:: rpy2.robjects.functions.Function(*args, **kwargs)
   :show-inheritance:
   :members:

.. autoclass:: rpy2.robjects.functions.SignatureTranslatedFunction(*args, **kwargs)
   :show-inheritance:
   :members:

.. index::
   pair: robjects; Formula
   single: formula

.. _robjects-formula:

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

The class :class:`robjects.Formula` is representing an `R` formula.

.. code-block:: python

  x = robjects.Vector(array.array('i', range(1, 11)))
  y = x.ro + rnorm(10, sd=0.2)

  fmla = robjects.Formula('y ~ x')
  env = fmla.environment
  env['x'] = x
  env['y'] = y

  stats = importr('lm')
  fit = stats.lm(fmla)

One drawback with that approach is that pretty printing of
the `fit` object is note quite as clear as what one would
expect when working in `R`.
However, by evaluating R code on
the fly, we can obtain a `fit` object that will display
nicely:

.. code-block:: python

   fit = robjects.r('lm(%s)' %fmla.r_repr())

.. autoclass:: rpy2.robjects.Formula(formula, environment = rinterface.globalenv)
   :show-inheritance:
   :members:

.. _robjects-packages:

R packages
==========

Importing R packages
--------------------

In R, objects can be bundled into packages for distribution.
In similar fashion to Python modules, the packages can be installed,
and then loaded when their are needed. This is achieved by the R
functions *library()* and *require()* (attaching the namespace of
the package to the R `search path`).

.. code-block:: python

   from rpy2.robjects.packages import importr
   utils = importr("utils")

The object :obj:`utils` is now a module-like object, in the sense that
its :attr:`__dict__` contains keys corresponding to the R symbols.
For example the R function *data()* can be accessed like:

>>> utils.data
<SignatureTranslatedFunction - Python:0x913754c / R:0x943bdf8>

Unfortunately, accessing an R symbol can be a little less straightforward
as R symbols can contain characters that are invalid in Python symbols.
Anyone with experience in R can even add there is a predilection for
the dot (*.*).

In an attempt to address this, during the import of the package a
translation of the R symbols is attempted, with dots becoming underscores.
This is not unlike what could be found in :mod:`rpy`, but with distinctive
differences: 

- The translation is performed once, when the package is imported,
  and the results cached. The caching allows us to perform the check below.

- A check that the translation is not masking other R symbols in the package
  is performed (e.g., both 'print_me' and 'print.me' are present).
  Should it happen, a :class:`rpy2.robjects.packages.LibraryError` is raised,
  the optional argument *robject_translations* to :func:`importr`
  shoud be used.

- The translation is concerning one package, limiting the risk
  of masking when compared to rpy translating relatively blindly and 
  retrieving the first match

.. note:: 

   The translation of '.' into '_' is clearly not sufficient, as
   R symbols can use a lot more characters illegal in Python symbols.
   Those more exotic symbols can be accessed through :attr:`__dict__`.
   
   Example:

   >>> utils.__dict__['?']
   <Function - Python:0x913796c / R:0x9366fac>

In addition to the translation of robjects symbols,
objects that are R functions see their named arguments translated as similar way
(with '.' becoming '_' in Python).

>>> base = importr('base')
>>> base.scan._prm_translate
{'blank_lines_skip': 'blank.lines.skip',
 'comment_char': 'comment.char',
 'multi_line': 'multi.line',
 'na_strings': 'na.strings',
 'strip_white': 'strip.white'}


.. automodule:: rpy2.robjects.packages
   :members:

Finding where an R symbol is coming from
----------------------------------------

Knowing which object is effectively considered when a given symbol
is resolved can be of much importance in R, as the number of packages
attached grows and the use of the namespace accessors "::" and ":::" 
is not so frequent.

The function :func:`wherefrom` offers a way to find it:

>>> import rpy2.robjects.packages as rpacks
>>> env = rpacks.wherefrom('lm')
>>> env.do_slot('name')[0]
'package:stats'


.. note::

   This does not generalize completely, and more details regarding
   environment, and packages as environment should be checked
   Section :ref:`rinterface-sexpenvironment`.

Installing/removing R packages
------------------------------

R is shipped with a set of *recommended packages* 
(the equivalent of a standard library), but there is a large
(and growing) number of other packages available.

Installing those packages can done from within R, and
one will consult an R-related documentation if unsure of how to
do so.


Working with R's OOPs
=====================

Object-Oriented Programming can a achieved in R, but in more than
one way. Beside the *official* S3 and S4 systems, there is a rich
ecosystem of alternative implementations of objects (aroma, or proto
are two such systems).

S3 objects
----------

S3 objects are default R objects (i.e., not S4 instances) for which
an attribute "class" has been added.

>>> x = robjects.IntVector((1, 3))
>>> tuple(x.rclass)
('integer',)

Making the object x an instance of a class *pair*, itself inheriting from
*integer* is only a matter of setting the attribute:

>>> x.rclass = robjects.StrVector(("pair", "integer"))
>>> tuple(x.rclass)
('pair', 'integer')

Methods for *S3* classes are simply R functions with a name such as name.<class_name>,
the dispatch being made at run-time from the first argument in the function call.

For example, the function *plot.lm* plots objects of class *lm*. The call
*plot(something)* will see R extract the class name of the object something, and see
if a function *plot.<class_of_something>* is in the search path.

.. note::

   This rule is not strict as there can exist functions with a *dot* in their name
   and the part after the dot not correspond to an S3 class name. 


S4 objects
----------

S4 objects are a little more formal regarding their class definition, and all
instances belong to the low-level R type SEXPS4.

The definition of methods for a class can happen anytime after the class has
been defined (a practice something referred to as *monkey patching*
or *duck punching* in the Python world).

There are obviously many ways to try having a mapping between R classes and Python
classes, and the one proposed here is to make Python classes that inherit
:class:`rpy2.rinterface.methods.RS4`.

Since the S4 system allows polymorphic definitions of methods, that is for a given
method name there can exist several sets of possible arguments (and type for
the arguments), it currently
appears trickly to have an simple, automatic, and robust mapping of R
methods to Python methods. For the time being, one will rely on
human-written mappings, although some helpers are provided by rpy2.

.. note::
   More automation for reflecting S4 class definitions into Python is on the list
   of items to be worked on, so one may hope for more in a following release.


To make this a little more concrete, we take the R class `lmList`
in the package `lme4` and show how to write a Python wrapper for it.

.. warning::

   The R package `lme4` is not distributed with R, and will have to be installed
   for the example to work.

First, a bit of boilerplate code is needed. We obviously 
import the higher-level interface, as well the function 
:func:`rpy2.robjects.packages.importr`. The R class we want to represent
is defined in the 
:mod:`rpy2` modules and utilities. 

.. literalinclude:: _static/demos/s4classes.py
   :start-after: #-- setup-begin
   :end-before:  #-- setup-end

Once done, the Python class definition can be written.
In the first part of that code, we choose a static mapping of the
R-defined methods. The advantage for doing so is a bit of speed
(as the S4 dispatch mechanism has a cost), and the disadvantage
is that the a modification of the method at the R level would require
a refresh of the mappings concerned. The second part of the code
is wrapper to those mappings, where Python-to-R operations prior
to calling the R method can be performed.
In the last part of the class definition, a *static methods* is defined.
This is one way to have polymorphic constructors implemented.

.. literalinclude:: _static/demos/s4classes.py
   :start-after: #-- LmList-begin
   :end-before:  #-- LmList-end

Creating a instance of :class:`LmList` can now be achieved by specifying
a model as a :class:`Formula` and a dataset.

.. literalinclude:: _static/demos/s4classes.py
   :start-after: #-- buildLmList-begin
   :end-before:  #-- buildLmList-end

A drawback of the approach above is that the R "call" is stored,
and as we are passing the :class:`DataFrame` *sleepstudy* 
(and as it is believed to to be an anonymous structure by R) the call
is verbose: it comprises the explicit structure of the data frame
(try to print *lml1*). This becomes hardly acceptable as datasets grow bigger.
An alternative to that is to store the columns of the data frame into
the environment for the :class:`Formula`, as shown below:

.. literalinclude:: _static/demos/s4classes.py
   :start-after: #-- buildLmListBetterCall-begin
   :end-before:  #-- buildLmListBetterCall-end


.. autoclass:: rpy2.robjects.methods.RS4(sexp)
   :show-inheritance:
   :members:


Automated mapping of user-defined classes
-----------------------------------------

Once a Python class mirroring an R classis defined, the mapping can be made
automatic by adding new rules to the conversion system
(see Section :ref:`robjects-conversion`).





Object serialization
====================

The python pickling system can be used to serialize objects to disk,
and restore them from their serialized form.

.. code-block:: python

   import pickle
   import rpy2.robjects as ro

   x = ro.StrVector(('a', 'b', 'c'))
   base_help.fetch('sum')
   f = file('/tmp/foo.pso', 'w')
   pickle.dump(x, f)
   f.close()


   f = file('/tmp/foo.pso', 'r')
   x_again = pickle.load(f)
   f.close()


.. warning::

   Currently loading an object from a serialized form restores the object in
   its low-level form (as in :mod:`rpy2.rinterface`). Higher-level objects
   can be restored by calling the higher-level casting function
   :func:`rpy2.robjects.conversion.ri2py` (see :ref:`robjects-conversion`).


Class diagram
=============

.. inheritance-diagram:: rpy2.robjects rpy2.robjects.methods rpy2.robjects.vectors rpy2.robjects.functions
   :parts: 1

