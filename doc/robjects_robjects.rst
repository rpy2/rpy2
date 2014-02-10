
R objects
=========

The class :class:`rpy2.robjects.RObject`
can represent any R object, although it will often
be used for objects without any more specific representation
in Python/rpy2 (such as :class:`Vector`,
:class:`functions.Function`, :class:`Environment`).

The class inherits from the lower-level
:class:`rpy2.rinterface.Sexp`
and from :class:`rpy2.robjects.robject.RObjectMixin`, the later defining
higher-level methods for R objects to be shared by other higher-level
representations of R objects.

.. autoclass:: rpy2.robjects.robject.RObjectMixin
   :show-inheritance:
   :members:

.. autoclass:: rpy2.robjects.RObject
   :show-inheritance:
   :members:

