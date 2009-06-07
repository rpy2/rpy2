

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
at least familiar with one of the two.

.. _Python: http://www.python.org
.. _R: http://www.r-project.org

Having an interface between both languages, and benefit from the respective
libraries of one language while working in the other language, appeared
desirable and an early option to achieve it was the RSPython project, 
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

This effort can be seen as a redesign and rewrite of the RPy package.

Installation
============

Requirements
------------

Python version 2.4 or higher, as well as R-2.7.0 or higher are required.

Currently the development is mostly done on Linux and a bit MacOS X with the
following version for the softwares:

======== ========
Software Versions 
======== ========
 Python   2.5; 2.6 
 R        2.8; 2.9 
======== ========

gcc-4.3 is used for compiling the C parts.


Download
--------

In theory we could have available for download:

  * Source packages.

  * Pre-compiled binary packages for

    * Microsoft's Windows

    * Apple's MacOS X

    * Linux distributions

`rpy2` has been reported compiling successfully on all 3 platforms, provided
that development items such as Python headers and a C compiler are installed.


Check on the `Sourceforge download page <http://downloads.sourceforge.net/rpy>`_
what is available.


.. note::
   Choose files from the `rpy2` package, not `rpy`.


Linux precompiled binaries
--------------------------

Debian packages are available thanks to Dirk Eddelbuettel.
This is likely to mean that Ubuntu and other Debian-based
distributions will also have it in their repositories.

.. index::
  single: install;win32

Microsoft's Windows precompiled binaries
----------------------------------------

If available, the executable can be run; this will install the package
in the default Python installation.

At the time of writing, Microsoft Windows binaries are contributed 
by Laurent Oget (from Predictix) since version 2.0.0b1.

.. index::
  single: install;source

Install from source
-------------------

The source package is on the PYthon Package Index (PYPI), and the 
*easy_install* script can be used whenever available.
The shell command will then just be:

.. code-block:: bash

   easy_install rpy2


To install from a downloaded source archive `<rpy_package>` do in a shell:

.. code-block:: bash

  tar -xzf <rpy_package>.tar.gz
  cd <rpy_package>
  python setup.py build install

This will build the package, guessing the R HOME from
the R executable found in the PATH.

It is otherwise possible to give explicitly the location for the R HOME:

.. code-block:: bash

   python setup.py build --r-home /opt/packages/R/lib install


.. index::
  single: test;whole installation

Test an installation
--------------------

At any time, an installation can be tested as follows:

.. code-block:: python

  import rpy2.tests
  import unittest

  # the verbosity level can be increased if needed
  tr = unittest.TextTestRunner(verbosity = 1)
  suite = rpy2.tests.suite()
  tr.run(suite)

.. note::

   At the time of writing, few unit tests will fail with
   the release version. Their failure is forced, as running
   the tests will either:

   * leave R in a close-to-unusable state because terminating
   then starting again an embbeded R is apparently not possible.

   * cause a segfault (the case with numpy arrays of unicode
   characters)


.. warning::

   Win32 versions are still lacking some of the functionalities in the
   UNIX-alike versions, most notably the callback function for console
   input and output.

Contents
========

The package is made of several sub-packages or modules:

:mod:`rpy2.rpy_classic`
-----------------------

Higher-level interface similar to the one in RPy-1.x.
This is provided for compatibility reasons, as well as to facilitate the migration
to RPy2.


:mod:`rpy2.robjects`
--------------------

Higher-level interface, when ease-of-use matters most.


:mod:`rpy2.rinterface`
----------------------

Low-level interface to R, when speed and flexibility
matter most. Here the programmer gets close(r) to R's C-level
API.

:mod:`rpy2.rlike`
-----------------

Data structures and functions to mimic some of R's features and specificities



Design notes
============


When designing ryp2, attention was given to make:

- the use of the module simple from both a Python or R user's perspective

- minimize the need for knowledge about R, and the need for tricks and workarounds.

- the possibility to customize a lot while remaining at the Python level (without having to go down to C-level).


:mod:`rpy2.robjects` implements an extension to the interface in
:mod:`rpy2.rinterface` by extending the classes for R
objects defined there with child classes.

The choice of inheritance was made to facilitate the implementation
of mostly inter-exchangeable classes between :mod:`rpy2.rinterface`
and :mod:`rpy2.robjects`. For example, an :class:`rpy2.rinterface.SexpClosure`
can be given any :class:`rpy2.robjects.RObject` as a parameter while
any :class:`rpy2.robjects.RFunction` can be given any 
:class:`rpy2.rinterface.Sexp`. Because of R's functional basis, 
a container-like extension is also present.

The module :mod:`rpy2.rpy_classic` is using delegation, letting us
demonstrate how to extend :mod:`rpy2.rinterface` with an alternative
to inheritance.


Acknowledgements
================

Acknowledgements go to (alphabetical order):

 
Alexander Belopolsky. 
    His code contribution of an alternative RPy is acknowledged.
    I have found great inspiration in reading that code.

Contributors
    The help of people, donating time, ideas or software patches
    is much appreciated.
    Their names can be found in this documentation (mostly around the
    section Changes).

JRI
    The Java-R Interface, and its authors, as at several occasions
    its code was the most practical source of documentation
    regarding how to embed R. 

Nathaniel Smith
    Great patches, challenging and pertinent comments.

Walter Moreira, and Gregory Warnes
    For the original RPy and its maintainance through the years.


