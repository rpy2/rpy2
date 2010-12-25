.. module:: rpy2.interactive

****************
Interactive work
****************

Overview
========

R is very often used as an interactive toplevel, or read-eval-print loop (REPL).
When analyzing data this is kind of environment is extremely convenient as
the analyst often does not know beforehand what lies in the data and how this
is going to be discovered.

Python is can also be used in a similar fashion, but limitations of the
default Python console have lead to the creation of alternative consoles
and interactive development editors
(idle, ipython, bpython, emacs mode, komodo, ...).
Features such as code highlighting, autocompletion, and convenient display of
help strings or function signatures have made those valuable tools.

The package :mod:`rpy2.interactive` aims at interactive users, but can be used
in non-interactive code as well. It is trading trading flexibility
or performances for ease-of-use.
 
>>> import rpy2.interactive as r
>>> v = r.vectors.IntVector((1,2,3))
>>> r.importr('datasets')
rpy2.robjecs.packages.Package as a <module 'datasets' (built-in)>
>>> tuple(r.packages.datasets.trees.names)
('Girth', 'Height', 'Volume')

R vectors
=========

>>> import rpy2.interactive as r
>>> x = r.vectors.IntVector(range(10))


R packages
==========

R has a rich selection of packages, known in other computer
languages and systems as libraries.

R Packages can be:

- available in R repositories (public or private)

- installed 

- attached (loaded)

Available packages
------------------

R has a function to check was are the available packages.

.. note::

   To list the available packages, we have to load the package `utils`.
   See Section load-packages for details about loading packages

>>> import rpy2.interactive as r
>>> r.importr("utils")
>>> m = r.packages.utils.available_packages()

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

      m_bioc = r.packages.utils.available_packages(contriburl = r.packages.utils.contrib_url(repos))   



Installing packages
-------------------

.. note::

   To install a package for repositories, we have to load the package `utils`.
   See Section load-packages for details about loading packages


>>> import rpy2.interactive as r
>>> r.importr("utils")
>>> package_name = "lme4"
>>> r.packages.utils.install_packages(package_name)

Once a package is installed it will be available for future use without having
the need to install it again (unless a different version of R is used).


Loading installed packages
--------------------------

Loading installed R packages can be done through the function importr. 

>>> import rpy2.interactive as r
>>> r.importr("graphics")
rpy2.robjecs.packages.Package as a <module 'graphics' (built-in)>

The function returns a package object, and also adds a reference to it
in :attr:`r.packages`

>>> r.packages.graphics
rpy2.robjecs.packages.Package as a <module 'graphics' (built-in)>



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


Graphical User interface
========================


