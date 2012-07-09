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
  Should it happen, a :class:`rpy2.robjects.packages.LibraryError` is raised.
  To avoid this, use the optional argument *robject_translations*
	to :func:`importr`.

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


R namespaces
^^^^^^^^^^^^

In R, a `namespace` is describing something specific in which symbols can be
exported, or kept internal. A lot of recent R packages are declaring a
namespace but this is not mandatory, although recommended in some R
development circles.

Namespaces and the ability to control the export of symbols
were introduced several years ago in R and were probably meant
to address the relative lack of control on symbol encapsulation an R
programmer has. Without it importing a package is in R is like
systematically writing `import *` on all packages and modules used in Python,
that will predictably create potential problems as the number
of packages used is increasing.

Since Python does not generally have the same requirement by default,
:func:`importr` exposes all objects in an namespace, 
no matter they are exported or not.



Class diagram
^^^^^^^^^^^^^

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

Installing those packages must be done within R, see the R documentation.
As a quick help, installing an R package can be done by

.. code-block:: bash

   sudo R

And then in the R console:

.. code-block:: r

   install.packages('foo')

