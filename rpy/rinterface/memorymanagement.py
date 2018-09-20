import contextlib
from . import _rinterface_capi as _rinterface


class ProtectionTracker(object):

    def __init__(self):
        self._counter = 0

    def protect(self, cdata):
        cdata = _rinterface.rlib.Rf_protect(cdata)
        self._counter += 1
        return cdata

    def unprotect(self, n):
        if self._counter == 0:
            raise Exception('Protect count already == 0')
        self._counter -= 1
        _rinterface.rlib.Rf_unprotect(n)

    def unprotect_all(self):
        _rinterface.rlib.Rf_unprotect(self._counter)


@contextlib.contextmanager
def rmemory():
    pt = ProtectionTracker()
    try:
        yield pt
    finally:
        pt.unprotect_all()
