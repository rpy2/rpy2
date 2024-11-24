import pytest
from . import utils
import rpy2.rinterface as rinterface

rinterface.initr()


def _just_pass(x):
    pass


@pytest.fixture(scope='module')
def silent_console_print():
    with utils.obj_in_module(rinterface.callbacks,
                             'consolewrite_print',
                             _just_pass):
        yield


def test_from_pyobject():
    pyobject = 'ahaha'
    sexp_new = rinterface.SexpExtPtr.from_pyobject(pyobject)
    # R External pointers are never copied.
    assert rinterface.RTYPES.EXTPTRSXP == sexp_new.typeof


def test_from_pyobject_new_tag():
    pyobject = 'ahaha'
    sexp_new = (rinterface.SexpExtPtr
                .from_pyobject(pyobject,
                               tag='b'))
    assert sexp_new.typeof == rinterface.RTYPES.EXTPTRSXP
    assert sexp_new.TYPE_TAG == 'b'


def test_from_pyobject_invalid_tag():
    pyobject = 'ahaha'
    with pytest.raises(TypeError):
        rinterface.SexpExtPtr.from_pyobject(pyobject, tag=True)


@pytest.mark.skip(reason='WIP')
def test_from_pyobject_protected():
    pyobject = 'ahaha'
    sexp_new = (rinterface.SexpExtPtr
                .from_pyobject(pyobject,
                               protected=rinterface.StrSexpVector("c")))
    assert sexp_new.typeof == rinterface.RTYPES.EXTPTRSXP
    assert sexp_new.__protected__[0] == 'c'


@pytest.mark.skip(reason='WIP')
def test_from_pyobject_invalid_protected():
    pyobject = 'ahaha'
    with pytest.raises(TypeError):
        rinterface.SexpExtPtr.from_pyobject(pyobject, protected=True)
