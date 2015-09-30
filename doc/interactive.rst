****************
Interactive work
****************

Overview
========

.. note::

   This is an experimental package, and some of the ideas experimented
   here have already made it to :mod:`rpy2.robjects`.

   For interactive work the "R magic" extension to `ipython` is
   the preferred way / most tested way for interactive work.

.. module:: rpy2.ipython

IPython magic integration (was rmagic)
======================================

.. automodule:: rpy2.ipython.rmagic
   :members:

.. module:: rpy2.interactive.process_revents
   :synopsis: Processing R events for interactivity

.. _interactive-reventloop:

R event loop
============

.. codeauthor:: Thomas Kluyver, Laurent Gautier

In order to perform operations like refreshing interactive graphical
devices, R need to process the events triggering the refresh.

>>> from rpy2.interactive import process_revents
>>> process_revents.start()

>>> from rpy2.robjects.packages import importr
>>> from rpy2.robjects.vectors import IntVector
>>> graphics = importr("graphics")
>>> graphics.barplot(IntVector((1,3,2,5,4)), ylab="Value")

Now the R graphical device is updated when resized.
Should one wish to stop processing the events:

>>> process_revents.stop()

The processing can be resumed, stopped again, and this repeated *ad libitum*.

The frequency with which the processing of R events is performed can be roughly
controlled. The thread is put to sleep for an arbitray duration between
each processing of R events.

>>> process_revents.EventProcessor.interval
0.2

This value can be changed and set to an other value if more or less frequent
processing is wished. This can be done while the threaded processing is
active and will be taken into account at the next sleep cycle.

>>> process_revents.EventProcessor.interval = 1.0

.. autofunction:: process_revents()



.. module:: rpy2.interactive

Utilities for interactive work
==============================

.. note:: 

   This module contains a number of experimental features, some of
   them no longer necessary since the "R magic" extension for ipython. 
   They are becoming deprecated, and will removed from the code base
   in future versions.

R is very often used as an interactive toplevel, or read-eval-print loop (REPL).
This is convenient when analyzing data: type some code, get the result,
type some new code and further analysis based on the results.

Python can also be used in a similar fashion, but limitations of the
default Python console have lead to the creation of alternative consoles
and interactive development editors
(idle, ipython, bpython, emacs mode, komodo, ...).
Features such as code highlighting, autocompletion, and convenient display of
help strings or function signatures have made those valuable tools.


The package :mod:`rpy2.interactive` aims at interactive users, but can be used
in non-interactive code as well. It is trading flexibility
or performances for ease-of-use.
 
>>> import rpy2.interactive as r
>>> import rpy2.interactive.packages # this can take few seconds
>>> v = r.IntVector((1,2,3))
>>> r.packages.importr('datasets')
rpy2.robjecs.packages.Package as a <module 'datasets' (built-in)>
>>> data = rpy2.interactive.packages.data
>>> rpackages = r.packages.packages
>>> # list of datasets
>>> data(rpackages.datasets).names()
# list here
>>> env = data(rpackages.datasets).fetch('trees')
>>> tuple(env['trees'].names)
('Girth', 'Height', 'Volume')

R vectors
---------

>>> import rpy2.interactive as r
>>> r.IntVector(range(10))
<IntVector - Python:0x935774c / R:0xa22b440>
[       0,        1,        2, ...,        7,        8,        9]
>>> r.IntVector(range(100))
<IntVector - Python:0xa1c2dcc / R:0x9ac5540>
[       0,        1,        2, ...,       97,       98,       99]

In R, there are no scalars.

>>> r.packages.base.pi
<FloatVector - Python:0xa1d7a0c / R:0x9de02a8>
[3.141593]

To know more, please check Section :ref:`introduction-vectors`.


R packages
----------

R has a rich selection of packages, known in other computer
languages and systems as libraries.

R Packages can be:

- available in R repositories (public or private)

- installed 

- attached (loaded)


Loading installed packages
^^^^^^^^^^^^^^^^^^^^^^^^^^

When starting R, the *base* package as well as by default the packages
*grDevices*, *graphics*, *methods*, *stats*, and *utils* are loaded.

We start with the loading of R packages since this is a very common
operation in R, and since R is typically distributed
with *recommended* packages one can immediately start playing with.

Loading installed R packages can be done through the function :func:`importr`. 

>>> import rpy2.interactive as r
>>> import rpy2.interactive.packages # this can take few seconds
>>> r.packages.importr("cluster")
rpy2.robjecs.packages.Package as a <module 'cluster' (built-in)>

The function returns a package object, and also adds a reference to it
in :attr:`r.packages.packages`

>>> rlib = r.packages.packages
>>> rlib.cluster
rpy2.robjecs.packages.Package as a <module 'cluster' (built-in)>

All objects in the R package *cluster* can subsequently be accessed
through that namespace object. For example, for the function barplot:

>>> rlib.cluster.silhouette
<SignatureTranslatedFunction - Python:0x24f9418 / R:0x2f5b008>


Similarly, other packages such as *nlme*, and *datasets*
can be loaded.

>>> r.packages.importr("nlme")
rpy2.robjecs.packages.Package as a <module 'stats' (built-in)>
>>> r.packages.importr("datasets")
rpy2.robjecs.packages.Package as a <module 'datasets' (built-in)>

We can then demonstrate how to access objects in R packages through
a graphical example:

.. code-block:: python

   r.packages.graphics.coplot(r.Formula('Time ~ conc | Wt'),
                              r.packages.datasets.Theoph) 



Available packages
^^^^^^^^^^^^^^^^^^

R has a function to list the available packages.

>>> import rpy2.interactive as r
>>> import rpy2.interactive.packages # this can take few seconds
>>> r.packages.importr("utils")
>>> rlib = r.packages.packages
>>> m = rlib.utils.available_packages()

The object returned is a :class:`rpy2.robjects.vectors.Matrix`, with one
package per row (there are many packages in the default CRAN repository).

>>> tuple(m.dim)
(2692, 13)

>>> tuple(m.colnames)
('Package', 'Version', 'Priority', 'Depends', 'Imports', 'LinkingTo', 'Suggests', 'Enhances', 'OS_type', 'License', 'Archs', 'File', 'Repository')


.. note::

   Specific repositories can be specified.

   For example with bioconductor.

   .. code-block:: python

      import rpy2.rinteractive as r

      bioc_rooturl = "http://www.bioconductor.org/packages"
      bioc_version = "2.7"
      bioc_sections = ("bioc", "data/annotation", "data/experiment", "extra")
   
      repos = r.vectors.StrVector(["/".join((bioc_rooturl, bioc_version, x)) for x in bioc_sections])   

      m_bioc = rlib.utils.available_packages(contriburl = r.packages.utils.contrib_url(repos))   



Installing packages
^^^^^^^^^^^^^^^^^^^

.. note::

   To install a package for repositories, we have to load the package `utils`.
   See Section load-packages for details about loading packages


>>> import rpy2.interactive as r
>>> import rpy2.interactive.packages # this can take few seconds
>>> rlib = r.packages.packages
>>> r.packages.importr("utils")
>>> package_name = "lme4"
>>> rlib.utils.install_packages(package_name)

Once a package is installed it is available for future use without having
the need to install it again (unless a different version of R is used).


