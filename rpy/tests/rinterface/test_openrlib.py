import pytest

from rpy2.rinterface_lib import openrlib
import rpy2.rinterface


def test_dlopen_invalid():
    with pytest.raises(ValueError):
        openrlib._dlopen_rlib(None)


def test_get_dataptr_fallback():
    with pytest.raises(NotImplementedError):
        openrlib._get_dataptr_fallback(None)


def test_get_symbol_or_fallback():
    func = openrlib._get_symbol_or_fallback('thereisnosuchsymbol',
                                            lambda x: 'fallback')
    assert func(None) == 'fallback'


def test_get_integer_elt_fallback():
    rpy2.rinterface.initr()
    v = rpy2.rinterface.IntSexpVector([1, 2, 3])
    assert (openrlib.INTEGER_ELT(v.__sexp__._cdata, 1)
            ==
            openrlib._get_integer_elt_fallback(v.__sexp__._cdata, 1))


def test_get_logical_elt_fallback():
    rpy2.rinterface.initr()
    v = rpy2.rinterface.BoolSexpVector([True, True, False])
    assert (openrlib.LOGICAL_ELT(v.__sexp__._cdata, 1)
            ==
            openrlib._get_logical_elt_fallback(v.__sexp__._cdata, 1))


def test_get_real_elt_fallback():
    rpy2.rinterface.initr()
    v = rpy2.rinterface.FloatSexpVector([1.1, 2.2, 3.3])
    assert (openrlib.REAL_ELT(v.__sexp__._cdata, 1)
            ==
            openrlib._get_real_elt_fallback(v.__sexp__._cdata, 1))
