.. module:: rpy2.rinterface
   :platform: Unix, Windows
   :synopsis: Low-level interface with R



*******************
Low-level interface
*******************


Overview
========

The package :mod:`rinterface` is provided as a lower-level interface,
for situations where either the use-cases addressed by :mod:`robjects`
are not covered, or for the cases where the layer in :mod:`robjects`
has an excessive cost in terms of performances.

The package can be imported with:

>>> import rpy2.rinterface as rinterface


.. index::
   single: initialization

Initialization
--------------

One has to initialize R before much can be done.
The function :func:`initr` lets one initialize
the embedded R.

This is done with the function :meth:`initr`.


.. autofunction:: initr()


>>> rinterface.initr()

Initialization should only be performed once. 
To avoid unpredictable results when using the embedded R, 
subsequent calls to :func:`initr` will not have any effect.

The functions :func:`get_initoptions` and :func:`set_initoptions`
can be used to modify the options.
Default parameters for the initialization are otherwise
in the module variable `initoptions`.



.. index::
   single: initialize R_HOME

.. note::
   If calling :func:`initr` returns an error stating that
   :envvar:`R_HOME` is not defined, you should either have the :program:`R` executable in
   your path (:envvar:`PATH` on unix-alikes, or :envvar:`Path` on Microsoft Windows) or
   have the environment variable :envvar:`R_HOME` defined. 

Ending R
^^^^^^^^

Ending the R process is possible, but starting it again with
:func:`initr` does appear to lead to an R process that is hardly usable.
For that reason, the use of :func:`endEmbeddedR` should be considered
carefully, if at all.

R space and Python space
------------------------

When using the RPy2 package, two realms are co-existing: R and Python.

The :class:`Sexp_Type` objects can be considered as Python envelopes pointing
to data stored and administered in the R space.

R variables are existing within an embedded R workspace, and can be accessed
from Python through their python object representations.

We distinguish two kind of R objects: named objects and anonymous objects. 
Named objects have an associated symbol in the R workspace.

Named objects
^^^^^^^^^^^^^

For example, the following R code is creating two objects, named `x` and `hyp`
respectively, in the `global environment`.
Those two objects could be accessed from Python using their names.

.. code-block:: r

   x <- c(1,2,3)

   hyp <- function(x, y) sqrt(x^2 + y^2)

Two environments are provided as :class:`rpy2.rinterface.SexpEnvironment`

.. index::
   single: globalEnv
   single: SexpEnvironment; globalEnv

.. rubric:: globalEnv

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

.. rubric:: baseNamespaceEnv

The base package has a namespace, that can be accessed as an environment.

.. note::
   Depending on what is in `globalEnv` and on the attached packages, base
   objects can be masked when starting the search from `globalEnv`. 
   Use `baseNamespaceEnv`
   when you want to be sure to access a function you know to be
   in the base namespace.


Anonymous objects
^^^^^^^^^^^^^^^^^

Anonymous R objects do not have an associated symbol, yet are protected
from garbage collection.

Such objects can be created when using the constructor for an `Sexp*` class.



Interactive features
====================

The embedded R started from :mod:`rpy2` is interactive, which 
means that a number of interactive features present when working
in an interactive R console will be available for use.

Such features can be called explicitly by the :mod:`rpy2` user, but
can also be triggered indirectly, as some on the R functions will behave
differently when run interactively compared to when run in the so-called
*BATCH mode*.

I/O with the R console
----------------------


Output from the console
^^^^^^^^^^^^^^^^^^^^^^^

The default callback function, called :func:`rinterface.consolePrint`
is a simple write to :data:`sys.stdout`

.. autofunction:: consolePrint(x)

   :param x: :class:`str`
   :rtype: None

This can be changed with the function :meth:`setWriteConsole`,
letting one specify what do with output from the R console 
by a function.

The callback function should accept one argument of type string
(that is the string output to the console) and not return anything.

An example should make it obvious::

   buf = []
   def f(x):
       # function that append its argument to the list 'buf'
       buf.append(x)

   # output from the R console will now be appended to the list 'buf'
   rinterface.setWriteConsole(f)

   date = rinterface.baseNamespaceEnv['date']
   rprint = rinterface.baseNamespaceEnv['print']
   rprint(date())

   # the output is in our list (as defined in the function f above)
   print(buf)


   # restore default function
   rinterface.setWriteConsole(rinterface.consolePrint)

.. autofunction:: setWriteConsole(f)

.. autofunction:: getWriteConsole()

   :rtype: a callable

   .. versionadded:: 2.0.3

Flushing output from the console will be handled with

.. autofunction:: setFlushConsole(f)

   .. versionadded:: 2.0.3

.. autofunction:: getFlushConsole()

   :rtype: a callable

   .. versionadded:: 2.0.3


Input to the console
^^^^^^^^^^^^^^^^^^^^

The default callback for inputing data is :func:`rinterface.consoleRead`

.. autofunction:: consoleRead(prompt)

   :param prompt: :class:`str`
   :rtype: :class:`str`

User input to the console can be can be customized the very same way.

The callback function should accept one argument of type string (that is the
prompt string), and return a string (what was returned by the user).

.. autofunction:: setReadConsole(f)

.. autofunction:: getReadConsole()

   :rtype: a callable


Graphical devices
-----------------

Interactive graphical devices can be resized and the information they display
refreshed, provided that the embedded R process is instructed to process
pending interactive events.

Currently, the way to achieve this is to call the function
:func:`rinterface.process_revents` at regular intervals.

This can be taken care of by an higher-level interface, or can
be hacked quickly as::

   import rpy2.rinterface as rinterface
   import time

   def refresh():
       # Ctrl-C to interrupt
       while True:
           rinterface.process_revents()
           time.sleep(0.1)

The module :mod:`threading` offers a trivial way to dispatch the work
to a thread whenever a script is running::

   import threading
   
   t = threading.Timer(0.1, refresh)
   t.start()
   
.. autofunction:: process_revents()


Classes
=======


Sexp
----

The class :class:`Sexp` is the base class for all R objects.


.. class:: Sexp

   .. attribute:: __sexp__

      Opaque C pointer to the underlying R object

   .. attribute:: named

      `R` does not count references for its object. This method
      returns the `NAMED` value (an integer). 
      See the R-extensions manual for further details.

   .. attribute:: typeof

      Internal R type for the underlying R object

      .. doctest::

         >>> letters.typeof
         16

   .. method:: __deepcopy__(self)

      Make a *deep* copy of the object, calling the R-API C function
      :cfunc:`Rf_duplicate()` for copying the R object wrapped.

      .. versionadded:: 2.0.3

   .. method:: do_slot(name)

      R objects can be given attributes. In R, the function
      *attr* lets one access an object's attribute; it is
      called :meth:`do_slot` in the C interface to R. 

      :param name: string
      :rtype: instance of :class:`Sexp`

      >>> matrix = rinterface.globalEnv.get("matrix")
      >>> letters = rinterface.globalEnv.get("letters")
      >>> ncol = rinterface.SexpVector([2, ], rinterface.INTSXP)
      >>> m = matrix(letters, ncol = ncol)
      >>> [x for x in m.do_slot("dim")]
      [13, 2]
      >>>

   .. method:: do_slot_assign(name, value)

      Assign value to the slot with the given name, creating the slot whenver
      not already existing.

      :param name: string
      :param value: instance of :class:`Sexp`


   .. method:: rsame(sexp_obj)

      Tell whether the underlying R object for sexp_obj is the same or not.

      :rtype: boolean


.. .. autoclass:: rpy2.rinterface.Sexp
..   :members:



.. index::
   single: SexpVector
   single: rinterface; SexpVector


:class:`SexpVector`
-------------------

Overview
^^^^^^^^

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


R types
^^^^^^^

R vectors all have a `type`, sometimes referred to in R as a `mode`.
This information is encoded as an integer by R, but it can sometimes be
better for human reader to be able to provide a string.

.. function:: str_typeint(typeint)

   Return a string corresponding to a integer-encoded R type.

   :param typeint: integer (as returned by :attr:`Sexp.typeof`)
   :rtype: string


.. index::
   pair: rinterface;indexing

Indexing
^^^^^^^^

The indexing is working like it would on regular `Python`
tuples or lists.
The indexing starts at 0 (zero), which differs from `R`, 
where indexing start at 1 (one).

.. note::
   The *__getitem__* operator *[*
   is returning a Python scalar. Casting
   an *SexpVector* into a list is only a matter 
   of either iterating through it, or simply calling
   the constructor :func:`list`.


Common attributes
^^^^^^^^^^^^^^^^^

.. index::
   single: names;rinterface

.. rubric:: Names


In R, vectors can be named, that is each value in the vector
can be given a name (that is be associated a string).
The names are added to the other as an attribute (conveniently
called `names`), and can be accessed as such:

>>> options = rinterface.globalEnv.get("options")()
>>> option_names = options.do_slot("names")
>>> [x for x in options_names]

.. note::
   Elements in a name vector do not have to be unique. A Python
   counterpart is provided as :class:`rpy2.rlike.container.TaggedList`.

.. index::
   single: dim
   single: dimnames


.. rubric:: Dim and dimnames

In the case of an `array`, the names across the
respective dimensions of the object are accessible
through the slot named `dimnames`.



.. rubric:: Constructors

.. autoclass:: rpy2.rinterface.SexpVector(obj, sexptype, copy)
   :show-inheritance:
   :members:


Convenience classes are provided to create vectors of a given type:

.. autoclass:: rpy2.rinterface.StrSexpVector
   :show-inheritance:
   :members:

.. autoclass:: rpy2.rinterface.IntSexpVector
   :show-inheritance:
   :members:

.. autoclass:: rpy2.rinterface.FloatSexpVector
   :show-inheritance:
   :members:

.. autoclass:: rpy2.rinterface.BoolSexpVector
   :show-inheritance:
   :members:

.. index::
   single: SexpEnvironment
   single: rinterface; SexpEnvironment

:class:`SexpEnvironment`
------------------------



:meth:`__getitem__` / :meth:`__setitem__`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The *[* operator will only look for a symbol in the environment
without looking further in the path of enclosing environments.

The following will return an exception :class:`LookupError`:

>>> rinterface.globalEnv["pi"]

The constant *pi* is defined in R's *base* package,
and therefore cannot be found in the Global Environment.

The assignment of a value to a symbol in an environment is as
simple as assigning a value to a key in a Python dictionary:

>>> x = rinterface.Sexp_Vector([123, ], rinterface.INTSXP)
>>> rinterface.globalEnv["x"] = x


.. note::
   Not all R environment are hash tables, and this may
   influence performances when doing repeated lookups

.. note::
  a copy of the R object is made in the R space.

:meth:`__iter__`
^^^^^^^^^^^^^^^^

The object is made iter-able.

For example, we take the base name space (that is the environment
that contains R's base objects:

>>> base = rinterface.baseNameSpace
>>> basetypes = [x.typeof for x in base]


.. warning::

   In the current implementation the content of the environment
   is evaluated only once, when the iterator is created. Adding 
   or removing elements to the environment will not update the iterator
   (this is a problem, that will be solved in the near future).


:meth:`get`
^^^^^^^^^^^

Whenever a search for a symbol is performed, the whole
search path is considered: the environments in the list
are inspected in sequence and the value for the first symbol found
matching is returned.

Let's start with an example:

>>> rinterface.globalEnv.get("pi")[0]
3.1415926535897931

The constant `pi` is defined in the package `base`, that
is always in the search path (and in the last position, as it is
attached first). The call to :meth:`get` will
look for `pi` first in `globalEnv`, then in the next environment
in the search path and repeat this until an object is found or the
sequence of environments to explore is exhausted.

We know that `pi` is in the base namespace and we could have gotten
here directly from there:

>>> ri.baseNameSpaceEnv.get("pi")[0]
3.1415926535897931
>>> ri.baseNameSpaceEnv["pi"][0]
3.1415926535897931
>>> ri.globalEnv["pi"][0]
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
LookupError: 'pi' not found

`R` can look specifically for functions, which is happening when
a parsed function call is evaluated.
The following example of an `R` interactive session should demonstrate it:

.. code-block:: r

   > mydate <- "hohoho"
   > mydate()
   Error: could not find function "mydate"
   >
   > date <- "hohoho"
   > date()
   [1] "Sat Aug  9 15:27:40 2008"

The base function `date` is still found, although a non-function object
is present earlier on the search path.

The same behavior can be obtained from :mod:`rpy2`
with the optional parameter `wantFun` (specify that :meth:`get`
should return an R function).

>>> ri.globalEnv["date"] = ri.StrSexpVector(["hohoho", ])
>>> ri.globalEnv.get("date")[0]
'hohoho'
>>> ri.globalEnv.get("date", wantFun=True)
<rinterface.SexpClosure - Python:0x7f142aa96198 / R:0x16e9500>
>>> date = ri.globalEnv.get("date", wantFun=True)
>>> date()[0]
'Sat Aug  9 15:48:42 2008'


R packages as environments
^^^^^^^^^^^^^^^^^^^^^^^^^^

In a `Python` programmer's perspective, it would be nice to map loaded `R`
packages as modules and provide access to `R` objects in packages the
same way than `Python` object in modules are accessed.

This is unfortunately not possible in a robust way: the dot character `.`
can be used for symbol names in R (like pretty much any character), and
this can make an exact correspondance between `R` and `Python` names 
rather difficult.
:mod:`rpy` uses transformation functions that translates '.' to '_' and back,
but this can lead to complications since '_' can also be used for R symbols. 

There is a way to provide explict access to object in R packages, since
loaded packages can be considered as environments.

For example, we can reimplement in `Python` the `R` function 
returning the search path (`search`).

.. code-block:: python

   def rsearch():
       """ Return a list of package environments corresponding to the
       R search path. """
       spath = [ri.globalEnv, ]
       item = ri.globalEnv.enclos()
       while not item.rsame(ri.emptyEnv):
           spath.append(item)
	   item = item.enclos()
       spath.append(ri.baseNameSpaceEnv)
       return spath



As an other example, one can implement simply a function that
returns from which environment an object called by :meth:`get` comes
from.

.. code-block:: python

   def wherefrom(name, startenv=ri.globalEnv):
       """ when calling 'get', where the R object is coming from. """
       env = startenv
       obj = None
       retry = True
       while retry:
           try:
               obj = env[name]
               retry = False
           except LookupError, knf:
               env = env.enclos()
	       if env.rsame(ri.emptyEnv):
                   retry = False
               else:
                   retry = True
       return env       


>>> wherefrom('plot').do_slot('name')[0]
'package:graphics'
>>> wherefrom('help').do_slot('name')[0]
'package:utils'

.. note::
   Unfortunately this does not generalize to all cases: the base package does not have a name.

   >>> wherefrom('get').do_slot('name')[0]
   Traceback (most recent call last):
   File "<stdin>", line 1, in <module>
   LookupError: The object has no such attribute.

.. index::
   single: closure
   single: SexpClosure
   single: rinterface; SexpClosure
   pair: rinterface; function


.. _rinterface-functions:

Functions
---------

.. rubric:: A function with a context

In R terminology, a closure is a function (with its enclosing
environment). That enclosing environment can be thought of as
a context to the function.

>>> sum = rinterface.globalEnv.get("sum")
>>> x = rinterface.SexpVector([1,2,3], rinterface.INTSXP)
>>> s = sum(x)
>>> s[0]
6

.. rubric:: Named arguments

Named arguments to an R function can be specified just the way
they would be with any other regular Python function.

>>> rnorm = rinterface.globalEnv.get("rnorm")
>>> rnorm(rinterface.SexpVector([1, ], rinterface.INTSXP), 
          mean = rinterface.SexpVector([2, ], rinterface.INTSXP))[0]
0.32796768001636134

There are however frequent names for R parameters causing problems: all the names with a *dot*. using such parameters for an R function will either require
to:

* use the special syntax `**kwargs` on a dictionary with the named parameters

* use the method :meth:`rcall`.  


.. Index::
   single: rcall; order of parameters

.. rubric:: Order for named parameters

One point where function calls in R can differ from the ones in 
Python is that
all parameters in R are passed in the order they are in the call
(no matter whether the parameter is named or not),
while in Python only parameters without a name are passed in order.
Using the class :class:`ArgsDict` in the module :mod:`rpy2.rlike.container`,
together with the method :meth:`rcall`,
permits calling a function the same way it would in R. For example::

   import rpy2.rlike.container as rpc
   args = rpc.ArgsDict()
   args['x'] = rinterface.IntSexpVector([1,2,3], rinterface.INTSXP)
   args[None] = rinterface.IntSexpVector([4,5], rinterface.INTSXP)
   args['y'] = rinterface.IntSexpVector([6, ], rinterface.INTSXP)
   rlist = rinterface.baseNameSpaceEnv['list']
   rl = rlist.rcall(args.items())

>>> [x for x in rl.do_slot("names")]
['x', '', 'y']



.. index::
   single: closureEnv

.. rubric:: closureEnv

In the example below, we inspect the environment for the
function *plot*, that is the namespace for the
package *graphics*.

>>> plot = rinterface.globalEnv.get("plot")
>>> ls = rinterface.globalEnv.get("ls")
>>> envplot_list = ls(plot.closureEnv())
>>> [x for x in envplot_ls]
>>>

:class:`SexpS4`
---------------

Object-Oriented programming in R exists in several flavours, and one
of those is called `S4`.
It has its own type at R's C-API level, and because of that specificity
we defined a class. Beside that, the class does not provide much specific
features (see the pydoc for the class below). 

An instance's attributes can be accessed through the parent
class :class:`Sexp` method
:meth:`do_slot`.

.. autoclass:: rpy2.rinterface.SexpS4(obj)
   :show-inheritance:
   :members:


.. digraph:: rinterface_graph

   "Sexp" -> "SexpVector";
   "Sexp" -> "SexpEnvironment";
   "Sexp" -> "SexpClosure";
   "Sexp" -> "SexpS4";


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

.. warning::

   The following constants for missing values are currently all broken. Do not use them.

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

Vector types
^^^^^^^^^^^^

:const:`CPLXSXP`
  Complex 

:const:`INTSXP`
  Integer.

:const:`LGLSXP`
  Boolean (logical in the R terminology)

:const:`REALSXP`
  Numerical value (float / double)

:const:`STRSXP`
  String

:const:`VECSXP`
  List

:const:`LANGSXP`
  Language object.

:const:`EXPRSXP`
  Unevaluated expression.

Other types
^^^^^^^^^^^

:const:`CLOSXP`
  Function with an enclosure. Represented by :class:`rpy2.rinterface.SexpClosure`.

:const:`ENVSXP`
  Environment. Represented by :class:`rpy2.rinterface.SexpEnvironment`.

:const:`S4SXP`
  Instance of class S4. Represented by :class:`rpy2.rinterface.SexpS4`.


Types one should not meet
^^^^^^^^^^^^^^^^^^^^^^^^^

:const:`PROMSXP`
  Promise.

