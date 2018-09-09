import pytest
from . import utils
import rpy2.rinterface as rinterface

rinterface.initr()


def _just_pass(x):
    pass


@pytest.fixture(scope='module')
def silent_console_print():
    with utils.obj_in_module(rinterface.callbacks, 'consolewrite_print', _just_pass):
        yield


def test_init_default():
    pyobject = 'ahaha'
    sexp_new = rinterface.SexpExtPtr(pyobject)
    # R External pointers are never copied.
    assert rinterface.EXTPTRSXP == sexp_new.typeof


def test_new_tag():
    pyobject = 'ahaha'
    sexp_new = rinterface.SexpExtPtr(pyobject, 
                                     tag = rinterface.StrSexpVector('b'))
    assert  sexp_new.typeof == rinterface.EXTPTRSXP
    assert sexp_new.__tag__[0] == 'b'


def test_init_invalid_tag():
    pyobject = 'ahaha'
    with pytest.raises(TypeError):
        rinterface.SexpExtPtr(pyobject, tag = True)

    
def test_init_protected():
    pyobject = 'ahaha'
    sexp_new = rinterface.SexpExtPtr(pyobject, 
                                     protected = rinterface.StrSexpVector("c"))
    assert sexp_new.typeof == rinterface.EXTPTRSXP
    assert sexp_new.__protected__[0] == 'c'

    
def test_init_invalid_protected():
    pyobject = 'ahaha'
    with pytest.raises(TypeError):
        rinterface.SexpExtPtr(pyobject, protected = True)
