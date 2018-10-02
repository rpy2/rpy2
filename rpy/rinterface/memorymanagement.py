import contextlib
from . import _rinterface_capi as _rinterface


class ProtectionTracker(object):

    def __init__(self):
        self._counter = 0

    @property
    def count(self):
        return self._counter
    
    def protect(self, cdata):
        """Short-term protection of the R object pointer 
        from R's garbage collection."""
        cdata = _rinterface.rlib.Rf_protect(cdata)
        self._counter += 1
        return cdata

    def unprotect(self, n: int) -> None:
        """Unprotect the last n objects in the short-term
        protection stack."""
        if self._counter == 0:
            raise Exception('Protect count already == 0')
        if n > self._counter:
            raise ValueError('n > count')
        self._counter -= n
        _rinterface.rlib.Rf_unprotect(n)

    def unprotect_all(self) -> None:
        _rinterface.rlib.Rf_unprotect(self._counter)
        self._counter = 0


@contextlib.contextmanager
def rmemory():
    pt = ProtectionTracker()
    try:
        yield pt
    finally:
        pt.unprotect_all()
