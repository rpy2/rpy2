"""Interface to and utilities for R's memory management."""

import contextlib
from . import openrlib


# TODO: make it extend ContextManager and delete the function
#   rmemory ?
class ProtectionTracker(object):
    """Convenience class to keep track of R's C-level protection stack.

    Mixing this with direct calls to Rf_protect() and Rf_unprotect() in
    the C API from Python, or even using Rf_protect() and Rf_unprotect(),
    is strongly discouraged."""

    def __init__(self):
        self._counter = 0

    @property
    def count(self):
        """Return the count for the protection stack."""
        return self._counter

    def protect(self, cdata):
        """Pass-through function that adds the R object to the short-term
        stack of objects protected from garbase collection."""
        cdata = openrlib.rlib.Rf_protect(cdata)
        self._counter += 1
        return cdata

    def unprotect(self, n: int) -> None:
        """Release the n objects last added to the protection stack."""
        if n > self._counter:
            raise ValueError('n > count')
        self._counter -= n
        openrlib.rlib.Rf_unprotect(n)

    def unprotect_all(self) -> None:
        """Release the total count of objects this instance knows to be
        protected from the protection stack."""
        openrlib.rlib.Rf_unprotect(self._counter)
        self._counter = 0


@contextlib.contextmanager
def rmemory():
    pt = ProtectionTracker()
    try:
        yield pt
    finally:
        pt.unprotect_all()
