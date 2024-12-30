rpy2-rinterface
===============

About
-----

The `rpy2` package is a namespace package. This is the part of
that package that covers the "low-level" interface to R used in
`rpy2`. This provides mappings to access R's C-API and utilities to do
so safely. It is otherwise relatively easily to crash (segfault)
a process by calling R's C-API.

This "low-level" is used by the higher-level (more Pythonic)
interface `rpy2.robjects` and the extentions for ipython and jupyter
notebooks in `rpy2.ipython`. It can also be used to implement alternative
higher level interfaces, and with care be used in situation where
a minimal interface or maximum performance is wanted.


Installation
------------

To install this package from a Python package repository, just enter:

.. code-block:: bash

   pip install rpy2-rinterface


Developing solutions with this interface
----------------------------------------

The package uses type hints and should have a clean `mypy` check.
Whenever using this low interface, for example in services, using
type checking can help increase confidence about the solution developed.

Type checking does not provide complete guarantees though. R's C API
can bring a process to crash rather easily. Multithreading in particular
can do this in no time. Check the documentation or internet forums.
