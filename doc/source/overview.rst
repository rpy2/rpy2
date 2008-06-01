Overview
========

Background
----------

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

The present documentation covers RPy2, an evolution of RPy-1.x.
Naturally RPy2 is inspired by RPy, but also by A. Belopolskys's contributions
that were waiting to be included into RPy.

Contents
--------

The package is made of several sub-packages or modules:

:mod:`rpy2.rpy_classic`
^^^^^^^^^^^^^^^^^^^^^^^

Higher-level interface similar to the one in RPy-1.x.
This is provided for compatibility reasons, and facilitate the migration
to RPy2.


:mod:`rpy2.robjects`
^^^^^^^^^^^^^^^^^^^^

Higher-level interface, when ease-of-use matters most.


:mod:`rpy2.rinterface`
^^^^^^^^^^^^^^^^^^^^^^

Low-level interface to R, when speed and flexibility
matter most. Here the programmer gets close(r) to R's C
API.


