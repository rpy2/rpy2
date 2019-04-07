import pytest
import rpy2.robjects as robjects
rinterface = robjects.rinterface
import array

identical = rinterface.baseenv['identical']
Function = robjects.functions.Function


def test_init_invalid():
    with pytest.raises(ValueError):
        Function('a')


def test_init_from_existing():
    ri_f = rinterface.baseenv.find('sum')

    ro_f = Function(ri_f)

    assert identical(ri_f, ro_f)[0] == True


def test_call_with_sexp():
    ri_f = rinterface.baseenv.find('sum')
    ro_f = Function(ri_f)

    ro_v = robjects.IntVector(array.array('i', [1,2,3]))

    s = ro_f(ro_v)
    assert s[0] == 6


def test_formals():
    ri_f = robjects.r('function(x, y) TRUE')
    res = ri_f.formals()
    #FIXME: no need for as.list when paired list are handled
    res = robjects.r['as.list'](res)
    assert len(res) == 2
    n = res.names
    assert n[0] == 'x'
    assert n[1] == 'y'


def test_function():
    r_func = robjects.functions.Function(robjects.r('function(x, y) TRUE'))
    assert isinstance(r_func.__doc__, str)


def test_signaturestranslatedfunction():
    r_func = robjects.r('function(x, y) TRUE')
    stf = robjects.functions.SignatureTranslatedFunction(r_func)
    assert isinstance(r_func.__doc__, str)


def test_documentedstfunction():
    dstf = robjects.functions.DocumentedSTFunction(robjects.baseenv['sum'],
                                                   packagename='base')
    assert isinstance(dstf.__doc__, str)
