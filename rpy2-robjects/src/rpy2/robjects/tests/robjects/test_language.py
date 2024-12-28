import pytest
import rpy2.robjects as robjects
import rpy2.robjects.language as lg
from rpy2 import rinterface
from rpy2.rinterface_lib import embedded


@pytest.fixture(scope='module')
def clean_globalenv():
    yield
    for name in robjects.globalenv.keys():
        del robjects.globalenv[name]


def test_eval(clean_globalenv):
    code = """
    x <- 1+2
    y <- (x+1) / 2
    """
    res = lg.eval(code)
    assert 'x' in robjects.globalenv.keys()
    assert robjects.globalenv['x'][0] == 3
    assert 'y' in robjects.globalenv.keys()
    assert robjects.globalenv['y'][0] == 2

    
def testeval_in_environment(clean_globalenv):
    code = """
    x <- 1+2
    y <- (x+1) / 2
    """
    env = robjects.Environment()
    res = lg.eval(code, envir=env)
    assert 'x' in env.keys()
    assert env['x'][0] == 3
    assert 'y' in env.keys()
    assert env['y'][0] == 2


def test_LangVector_from_string():
    lang_obj = lg.LangVector.from_string('1+2')
    assert lang_obj.typeof == rinterface.RTYPES.LANGSXP


def test_LangVector_repr():
    lang_obj = lg.LangVector.from_string('1+2')
    assert repr(lang_obj) == 'Rlang( 1 + 2 )'


def test_LangVector_from_string_invalid():
    with pytest.raises(embedded.RRuntimeError):
        lang_obj = lg.LangVector.from_string(1)
