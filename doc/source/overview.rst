

********
Overview
********


Background
==========

`Python`_ is a popular
all-purpose scripting language, while `R`_ (an open source implementation
of the S/Splus language)
is a scripting language mostly popular for data analysis, statistics, and
graphics. If you are reading this, there are good chances that you are
at least familiar with one of both.

.. _Python: http://www.python.org
.. _R: http://www.r-project.org

Having an interface between both languages to benefit from the
libraries of one language while working in the other appeared
desirable; an early option to achieve it was the RSPython project,
itself part of the `Omegahat project`_.

A bit later, the RPy project appeared and focused on providing simple and
robust access to R from within Python, with the initial Unix-only releases
quickly followed by Microsoft and MacOS compatible versions.
This project is referred to as RPy-1.x in the
rest of this document.

.. _Omegahat project: http://www.omegahat.org/RSPython

The present documentation describes RPy2, an evolution of RPy-1.x.
Naturally RPy2 is inspired by RPy, but also by A. Belopolskys's contributions
that were waiting to be included into RPy.

This effort can be seen as a redesign and rewrite of the RPy package, and this
unfortunately means there is not enough left in common to ensure compatibility.


Installation
============

Upgrading from an older release of rpy2
---------------------------------------

In order to upgrade one will have to first remove older
installed rpy2 packages then and only then install
a version of rpy2.

To do so, or to check whether you have an earlier version
of rpy2 installed, do the following in a Python console:

.. code-block:: python

   import rpy2
   rpy2.__path__

An error during execution means that you do not have any older
version of rpy2 installed and you should proceed to the next section.

If this returns a string containing a path, you should go to that path
and remove all files and directories starting with *rpy2*. To make sure
that the cleaning is complete, open a new Python session and check that
the above code results in an error.


Requirements
------------

Currently the development is done on UNIX-like operating systems with the
following software versions. Those are the recommended
versions to run rpy2 with.

======== ===========
Software Versions
======== ===========
 Python   3.3
 R        2.16
======== ===========

Running Rpy2 will require compiled libraries for R, Python, and readline;
building rpy2 will require the corresponding development headers 
(check the documentation for more information about builing rpy2). 

Python versions < 3.3 are not supported. Consider using an earlier
version of rpy2 if you cannot / do not want to upgrade Python.

Rpy2 is not expected to work at all with an R version < 2.8. The use of the
latest rpy2 with an R version older than the current release is not
adviced (and is unsupported).

Alternative Python implementations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

CPython is the target implementation, and because of presence of C code
in rpy2 is it currently not possible to run the package on Jython.
For that same reason, running it with Pypy is expected to require
some effort.

Download
--------

The following options are, or could be, available for download:

  * Source packages. Released versions are available on Sourceforge as well as
    on Pypi. Snapshots of the development version can be downloaded from
    bitbucket

    .. note::
       The repository on bitbucket has several branches. Make sure to select
       the one you are interested in.

  * Pre-compiled binary packages for

    * Microsoft's Windows (releases are on Sourceforge, irregular snapshots
      for the dev version on bitbucket) - there is currently no support for
      this platform

    * Apple's MacOS X (although Fink and Macports are available, there does not
      seem to be binaries currently available)

    * Linux distributions

`rpy2` has been reported compiling successfully on all 3 platforms, provided
that development items such as Python headers and a C compiler are installed.

.. note::
   Choose files from the `rpy2` package, not `rpy`.

.. note::
   The *pip* or *easy_install* commands can be used,
   although they currently only provide installation from source
   (see :ref:`install-easyinstall`).

Linux precompiled binaries
--------------------------

Linux distribution have packaging systems, and rpy2 is present
in a number of them, either as a pre-compiled package or a source
package compiled on-the-fly.

.. note:: 

   Those versions will often be older than the latest rpy2 release.

Known distributions are: Debian and related (such as Ubuntu - often
the most recent thanks to Dirk Eddelbuettel), Suse, RedHat, Mandrake,
Gentoo.

On, OS X rpy2 is in Macports and Fink.


.. index::
  single: install;win32

Microsoft's Windows precompiled binaries
----------------------------------------

If available, the executable can be run; this will install the package
in the default Python installation.

For few releases in the 2.0.x series, Microsoft Windows binaries were contributed
by Laurent Oget from Predictix.

There is currently no binaries or support for Microsoft Windows (more for lack of
ressources than anything else).

.. index::
  single: install;source

Install from source
-------------------

.. _install-easyinstall:

easy_install and pip
^^^^^^^^^^^^^^^^^^^^

The source package is on the PYthon Package Index (PYPI), and the
*pip* or *easy_install* scripts can be used whenever available.
The shell command will then just be:

.. code-block:: bash

   # recommended:
   pip install rpy2

   # or
   easy_install rpy2


Upgrading an existing installation is done with:

.. code-block:: bash

	 # recommended:
   pip install rpy2 --upgrade

   # or
   easy_install rpy2 --upgrade

Both utilities have a list of options and their respective documentation should
be checked for details.


.. _install-setup:

source archive
^^^^^^^^^^^^^^

To install from a downloaded source archive `<rpy_package>`, do in a shell:

.. code-block:: bash

  tar -xzf <rpy_package>.tar.gz
  cd <rpy_package>
  python setup.py build install

This will build the package, guessing the R HOME from
the R executable found in the PATH.

Beside the regular options for :mod:`distutils`-way of building and installing
Python packages, it is otherwise possible to give explicitly the location for the R HOME:

.. code-block:: bash

   python setup.py build --r-home /opt/packages/R/lib install


Other options to build the package are:

.. code-block:: bash

   --r-home-lib # for exotic location of the R shared libraries

   --r-home-modules # for R shared modules


Compiling on Linux
^^^^^^^^^^^^^^^^^^

Given that you have the libraries and development headers listed above, this
should be butter smooth.

The most frequent errors seem to be because of missing headers.

Compiling on OS X
^^^^^^^^^^^^^^^^^

*XCode* tools will be required in order to compile rpy2. Please refer to the documentation on the Apple
site for more details about what they are and how to install them.

On OS X "Snow Leopard" (10.6.8), it was reported that setting architecture flags was sometimes needed

.. code-block:: bash

   env ARCHFLAGS="-arch i386 -arch x86_64" pip install rpy2

or 

.. code-block:: bash

   env ARCHFLAGS="-arch i386 -arch x86_64" python setup.py build install

Some people have reported trouble with OS X "Lion". Please check the bug tracker if you are in that situation.


Using rpy2 with other versions of R or Python
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


.. warning::

   When building rpy2, it is checked that this is against a recommended
   version of R. Building against a different version is possible, although
   not supported at all, through the flag *--ignore-check-rversion*

   .. code-block:: bash

      python setup.py build_ext --ignore-check-rversion install
   
   Since recently, development R is no longer returning
   an R version and the check ends with an error
   "Error: R >= <some version> required (and R told 'development.').".
   The flag *--ignore-check-rversion* is then required in order to build.
   

.. note::
   
   When compiling R from source, do not forget to specify
   *--enable-R-shlib* at the *./configure* step.




.. index::
  single: test;whole installation

Test an installation
--------------------

An installation can be tested for functionalities, and whenever necessary 
the different layers constituting the packages can be tested independently.

.. code-block:: bash

   python -m 'rpy2.tests'

On Python 2.6, this should return that all tests were successful.


Whenever more details are needed, one can consider running explicit tests.

.. code-block:: python

  import rpy2.tests
  import unittest

  # the verbosity level can be increased if needed
  tr = unittest.TextTestRunner(verbosity = 1)
  suite = rpy2.tests.suite()
  tr.run(suite)

.. note:: 

   Running the tests in an interactive session appears to trigger spurious exceptions
   when testing callback functions raising exceptions.
	 If unsure, simply use the former way to test (in a shell).

.. warning::

  For reasons that remain to be elucidated, running the test suites used to leave the Python
  interpreter in a fragile state, soon crashing after the tests have been run.

  It is not clear whether this is still the case, but is recommended to terminate the 
  Python process after the tests and start working with a fresh new session.


To test the :mod:`rpy2.robjects` high-level interface:

.. code-block:: bash

  python -m 'rpy2.robjects.tests.__init__'

or for a full control of options

.. code-block:: python

  import rpy2.robjects.tests
  import unittest

  # the verbosity level can be increased if needed
  tr = unittest.TextTestRunner(verbosity = 1)
  suite = rpy2.robjects.tests.suite()
  tr.run(suite)

If interested in the lower-level interface, the tests can be run with:

.. code-block:: bash

  python -m 'rpy2.rinterface.tests.__init__'

or for a full control of options

.. code-block:: python

  import rpy2.rinterface.tests
  import unittest

  # the verbosity level can be increased if needed
  tr = unittest.TextTestRunner(verbosity = 1)
  suite = rpy2.rinterface.tests.suite()
  tr.run(suite)


Contents
========

The package is made of several sub-packages or modules:

:mod:`rpy2.rinterface`
----------------------

Low-level interface to R, when speed and flexibility
matter most. Close to R's C-level API.

:mod:`rpy2.robjects`
--------------------

High-level interface, when ease-of-use matters most.
Should be the right pick for casual and general use.
Based on the previous one.

:mod:`rpy2.interactive`
-----------------------

High-level interface, with an eye for interactive work. Largely based
on :mod:`rpy2.robjects`.

:mod:`rpy2.rpy_classic`
-----------------------

High-level interface similar to the one in RPy-1.x.
This is provided for compatibility reasons, as well as to facilitate the migration
to RPy2.

:mod:`rpy2.rlike`
-----------------

Data structures and functions to mimic some of R's features and specificities
in pure Python (no embedded R process).



Design notes
============


When designing rpy2, attention was given to:

- render the use of the module simple from both a Python or R user's perspective,

- minimize the need for knowledge about R, and the need for tricks and workarounds,

- allow to customize a lot while remaining at the Python level (without having to go down to C-level).


:mod:`rpy2.robjects` implements an extension to the interface in
:mod:`rpy2.rinterface` by extending the classes for R
objects defined there with child classes.

The choice of inheritance was made to facilitate the implementation
of mostly inter-exchangeable classes between :mod:`rpy2.rinterface`
and :mod:`rpy2.robjects`. For example, an :class:`rpy2.rinterface.SexpClosure`
can be given any :class:`rpy2.robjects.RObject` as a parameter while
any :class:`rpy2.robjects.Function` can be given any
:class:`rpy2.rinterface.Sexp`. Because of R's functional basis,
a container-like extension is also present.

The module :mod:`rpy2.rpy_classic` is using delegation, letting us
demonstrate how to extend :mod:`rpy2.rinterface` with an alternative
to inheritance.


Acknowledgements
================

Acknowledgements for contributions, support, and early testing go to (alphabetical order):

Alexander Belopolsky,
Brad Chapman,
Peter Cock,
Dirk Eddelbuettel,
Thomas Kluyver,
Walter Moreira, 
Laurent Oget,
John Owens,
Nicolas Rapin,
Grzegorz Slodkowicz,
Nathaniel Smith,
Gregory Warnes,
as well as
the JRI author(s),
the R authors,
R-help list responders,
Numpy list responders,
and other contributors.
