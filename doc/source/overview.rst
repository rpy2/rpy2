Overview
========

`Python`_ is a popular 
all-purpose scripting language, while `R`_
is a scripting language mostly popular for data analysis, statistics, and
graphics.

.. _Python: http://www.python.org
.. _R: http://www.r-project.org

The RPy project is an effort to have access to R from within Python, 

The RPy code was initially inspired in RSPython, which is part of
the `Omegahat project`_.

.. _Omegahat project: http://www.omegahat.org/RSPython

RPy2 is inspired by RPy, as well as A. Belopolskys's contributions to RPy.
A compatibility layer with RPy is provided.

FIXME: write a section about what changed



The package is made of several elements:


:mod:`rpy_classic`
    Higher-level interface similar to the one in RPy-1.x

:mod:`robjects`
    Higher-level interface, when ease-of-use matters most


:mod:`rinterface`
    Low-level interface to R, when speed and flexibility
    matter most. Here the programmer gets close to R's C
    API, and can use R's function faster than within an R session.


