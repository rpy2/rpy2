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


@pytest.mark.parametrize(
    'rcls,value,func,fallback',
    ((rpy2.rinterface.IntSexpVector, [1, 2, 3],
      openrlib.INTEGER_ELT, openrlib._get_integer_elt_fallback),
     (rpy2.rinterface.BoolSexpVector, [True, True, False],
      openrlib.LOGICAL_ELT, openrlib._get_logical_elt_fallback),
     (rpy2.rinterface.FloatSexpVector, [1.1, 2.2, 3.3],
      openrlib.REAL_ELT, openrlib._get_real_elt_fallback)
    )
)
def test_get_vec_elt_fallback(rcls, value, func, fallback):
    rpy2.rinterface.initr()
    v = rcls(value)
    assert (func(v.__sexp__._cdata, 1)
            ==
            fallback(v.__sexp__._cdata, 1))


@pytest.mark.parametrize(
    'rcls,value,func,getter',
    ((rpy2.rinterface.IntSexpVector, [1, 2, 3],
      openrlib._set_integer_elt_fallback,
      openrlib._get_integer_elt_fallback),
     (rpy2.rinterface.BoolSexpVector, [True, True, False],
      openrlib._set_logical_elt_fallback,
      openrlib._get_logical_elt_fallback),
     (rpy2.rinterface.FloatSexpVector, [1.1, 2.2, 3.3],
      openrlib._set_real_elt_fallback,
      openrlib._get_real_elt_fallback)
    )
)
def test_set_vec_elt_fallback(rcls, value, func, getter):
    rpy2.rinterface.initr()
    v = rcls(value)
    func(v.__sexp__._cdata, 1, value[2])
    assert getter(v.__sexp__._cdata, 1) == value[2]

