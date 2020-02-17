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


@pytest.mark.parametrize(
    'r_code,parameter_names,valid_kwargs',
    (
        ('function(x, y=FALSE, z="abc") TRUE', ('x', 'y', 'z'), True),
        ('function(x, y=FALSE, z="abc") {TRUE}', ('x', 'y', 'z'), True),
        ('function(x, ..., y=FALSE, z="abc") TRUE', ('x', '___', 'y', 'z'), True),
        ('function(x, y=FALSE, z, ...) TRUE', ('x', 'y', 'z', '___'), False)
    )
)
@pytest.mark.parametrize('map_defaults', (True, False))
def test_map_signature(r_code, parameter_names, valid_kwargs, map_defaults):
    r_func = robjects.r(r_code)
    stf = robjects.functions.SignatureTranslatedFunction(r_func)
    if not valid_kwargs:
        with pytest.raises(ValueError):
            signature = robjects.functions.map_signature(r_func, map_defaults=map_defaults)
    else:
        signature = robjects.functions.map_signature(r_func, map_defaults=map_defaults)
        assert tuple(signature.parameters.keys()) == parameter_names


@pytest.mark.parametrize('full_repr', (True, False))
@pytest.mark.parametrize('method_of', (True, False))
def test_wrap_r_function(full_repr, method_of):
    r_code = 'function(x, y=FALSE, z="abc") TRUE'
    parameter_names = ('x', 'y', 'z')
    r_func = robjects.r(r_code)
    stf = robjects.functions.SignatureTranslatedFunction(r_func)
    foo = robjects.functions.wrap_r_function(r_func, 'foo',
                                             full_repr=full_repr)
    assert foo._r_func.rid == r_func.rid
    assert tuple(foo.__signature__.parameters.keys()) == parameter_names
