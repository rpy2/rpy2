import pytest
from rpy2 import rinterface
from rpy2.rinterface import memorymanagement

rinterface.initr()


def test_rmemory_manager():
    with memorymanagement.rmemory() as rmemory:
        assert rmemory.count == 0
        foo = rmemory.protect(rinterface.conversion._str_to_charsxp('foo'))
        assert rmemory.count == 1
        del(foo)
    assert rmemory.count == 0


def test_rmemory_manager_unprotect():
    with memorymanagement.rmemory() as rmemory:
        assert rmemory.count == 0
        foo = rmemory.protect(rinterface.conversion._str_to_charsxp('foo'))
        with pytest.raises(ValueError):
            rmemory.unprotect(2)
        rmemory.unprotect(1)
        assert rmemory.count == 0
        del(foo)
    assert rmemory.count == 0


def test_rmemory_manager_unprotect_invalid():
    with memorymanagement.rmemory() as rmemory:
        assert rmemory.count == 0
        with pytest.raises(ValueError):
            rmemory.unprotect(2)
    assert rmemory.count == 0
