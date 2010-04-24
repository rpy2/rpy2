****************
Related projects
****************


rnumpy
======

The :mod:`rnumpy` interface builds on :mod:`rpy2.rinterface`
and offers a different approach to the one in :mod:`rpy2.robjects`.

Users familiar with :mod:`numpy` and with working in interactive sessions 
with *ipython* (more on ipython at :ref:`interactive-sessions`) 
will want to have a look at it.

More details can be found on the 
`rnumpy page <http://bitbucket.org/njs/rnumpy/wiki/Home>`_

Bioconductor
============

Bioconductor is a popular set of R packages for bioinformatics.
A number of classes defined within that project are exposed as Python classes through rpy2,
in the project `rpy2-bioconductor-extensions http://pypi.python.org/pypi/rpy2-bioconductor-extensions/0.2-dev`_.


.. _interactive-sessions:

Interactive consoles
====================

Data analysts often like to work interactively, that is going through short
cycles like:

* write a bit of code, which can be mostly involving a call to an existing function

* run that code

* inspect the results, often using plots and figures

R users will be particularly familiar with this sort of approach, and will likely
want it when working with :mod:`rpy2`.

Obviously the Python console can be used, but there exist improvements to it, making
the user experience more pleasant with features such as history and autocompletion.
Example of such enhanced consoles are:

* ipython: interactive-python shell, developed under of the `scipy <http://scipy.org>`
  (Scientific Python) umbrella

* bpython: curse-based enhancement to the Python console

* emacs: the Emacs text editor can be used to host a python session, 
  or an ipython session


Embeddeding an R console
------------------------

Python can be used to develop full-fledged applications, including applications with
a graphical user interface. 

:mod:`rpy2` can be used to provide an R console embedded in such applications, 
or build an alternative R GUI.

When offering an R console, the developer(s) may want to retain control on the
the way interaction with R is handled, at the level of the console and for the
base R functions targetting interactivity (see Section  :ref:`rinterface-callbacks`).
