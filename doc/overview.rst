

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
at least familiar with one or both.

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
Naturally RPy2 is inspired by RPy, but also by Alexander Belopolsky's contributions
that were waiting to be included into RPy.

This effort can be seen as a redesign and rewrite of the RPy package, and this
unfortunately means there is not enough left in common to ensure compatibility.


.. _install-installation:

Installation
============


Docker image
------------

There are few Docker images available to try rpy2 out
without even reading about requirements (e.g., R installed
compiled with the shared library flag). The Docker images
can also be an easy start for Windows users.

More information is available here: https://github.com/rpy2/rpy2-docker

	   
Requirements
------------

Currently the development is done on UNIX-like operating systems with the
following software versions. Those are the recommended
versions to run rpy2 with.

======== =====================================================================
Software Versions
======== =====================================================================
 Python   >=3.7
 R        >=4.0
======== =====================================================================

Running Rpy2 will require compiled libraries for R, Python, and readline;
building rpy2 will require the corresponding development headers 
(check the documentation for more information about builing rpy2). 

.. note::

   Running `rpy2` on Windows is currently not supported although relative success
   was recently reported with the lastest in the 3.3.x series. 


Alternative Python implementations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

CPython is the target implementation, and because of presence of C code
in rpy2 is it currently not possible to run the package on Jython.
For that same reason, running it with Pypy is expected to require
some effort.

Upgrading from an older release of rpy2
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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


Download
--------

The following options are available for download:

  * Source packages. Released versions are available on Pypi
    (Sourceforge is no longer used).
    Snapshots of the development version can be downloaded from
    github

    .. note::
       The repository on bitbucket has several release branches
       starting with `v`.

  * Pre-compiled binary packages for

    * Apple's MacOS X are now also available on pypi

    * Linux distributions are sometimes available. Check with your distribution


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

OS X (MacOS) precompiled binaries
---------------------------------

rpy2 is in Macports, Homebrew, and Fink. Binary are now also availabe on pypi.


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

   # minimal
   pip install rpy2

   # or
   # to run tests
   pip install rpy2[test]

   # or
   # all dependencies
   pip install rpy2[all]


Upgrading an existing installation is done with:

.. code-block:: bash

	 # recommended:
   pip install rpy2 --upgrade


Both utilities have a list of options and their respective documentation should
be checked for details.

.. note::

   Starting with rpy2 3.2.0, rpy2 can built and used with :mod:`cffi`'s ABI or
   API modes (releases 3.0.x and 3.1.x were using the ABI mode exclusively).
   At the time of writing the default is still the ABI mode but the choice
   can be controlled through the environment variable
   `RPY2_CFFI_MODE`. If set, possible values are `ABI` (default if the environment
   variable is not set), `API`, or `BOTH`. When the latter, both `API` and `ABI`
   modes are built, and the choice of which one to use can be made at run time.

.. _install-setup:

source archive
^^^^^^^^^^^^^^

To install from a downloaded source archive `<rpy_package>`, do in a shell:

.. code-block:: bash

  tar -xzf <rpy_package>.tar.gz
  cd <rpy_package>

  
  python setup.py build install
  # or
  pip install .
  # or (to install requirements to test
  pip install .[test]

  

This will build the package, guessing the R HOME from
the R executable found in the `PATH`.


Compiling on Linux
^^^^^^^^^^^^^^^^^^

Given that you have the libraries and development headers listed above, this
should be butter smooth.

The most frequent errors seem to be because of missing headers.


Compiling on OS X
^^^^^^^^^^^^^^^^^

*XCode* tools will be required in order to build rpy2 in API mode. Please refer to the documentation on the Apple
site for more details about what they are and how to install them.

.. index::
  single: test;whole installation

Test an installation
--------------------

An installation can be tested for functionalities, and whenever necessary 
the different layers constituting the packages can be tested independently.

.. code-block:: bash

   pytest --pyargs 'rpy2.tests'

The documentation for `pytest` should be consulted to customize how
tests are run.

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

However, inheritance is not the only choice. Any custome class implementing
the interface :class:`rpy2.rinterface.SupportsSEXP` can integrate seamlessly
and be used with the rest of rpy2.


Acknowledgements
================

Acknowledgements for contributions, support, and early testing go to (alphabetical order):

Philipp A.,
Alexander Belopolsky,
Dan Brown,
Beau Bruce,
Brad Buran,
Erik Cederstrand,
Brad Chapman,
Evgeny Cherkashin,
Dav Clark,
Peter Cock,
Michaël Defferrard,
Dirk Eddelbuettel,
Isuru Fernando,
Daniel Ge,
Christoph Gohlke,
Dale Jung,
Thomas Kluyver,
David Koppstein,
Michał Krassowski,
Antony Lee,
Kenneth Lyons,
Mikolaj Magnuski,
Gijs Molenaar,
Walter Moreira, 
Laurent Oget,
Pablo Oliveira,
John Owens,
Fabian Philips,
Andrey Portnoy,
Nicolas Rapin,
Brad Reisfeld,
Joon Ro,
Andy Shapiro,
Justin Shenk,
Grzegorz Slodkowicz,
Joan Smith,
Nathaniel J. Smith,
Jeff Tratner,
Gregory Warnes,
Liang-Bo Wang,
as well as
the JRI author(s),
the R authors,
R-help list responders,
Numpy list responders,
and other contributors.
