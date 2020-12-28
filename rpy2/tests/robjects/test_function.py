import pytest
import inspect
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
    'value, expected',
    ((robjects.r('TRUE'), True),
     (robjects.r('1'), 1),
     (robjects.r('"abc"'), 'abc'))
)
def test_map_default_values(value, expected):
    assert robjects.functions._map_default_value(value) == expected


@pytest.mark.parametrize(
    'r_code,parameter_names,r_ellipsis',
    (
        ('function(x, y=FALSE, z="abc") TRUE', ('x', 'y', 'z'), None),
        ('function(x, y=FALSE, z="abc") {TRUE}', ('x', 'y', 'z'), None),
        ('function(x, ..., y=FALSE, z="abc") TRUE', ('x', '___', 'y', 'z'), 1),
    )
)
def test_map_signature(r_code, parameter_names, r_ellipsis):
    r_func = robjects.r(r_code)
    stf = robjects.functions.SignatureTranslatedFunction(r_func)
    signature, r_ellipsis = robjects.functions.map_signature(r_func)
    assert tuple(signature.parameters.keys()) == parameter_names


@pytest.mark.parametrize(
    'r_code,parameter_names',
    (
         ('function(x, y=FALSE, z, ...) TRUE', ('x', 'y', 'z', '___')),
    )
)
def test_map_signature_invalid(r_code, parameter_names):
    r_func = robjects.r(r_code)
    stf = robjects.functions.SignatureTranslatedFunction(r_func)
    with pytest.raises(ValueError):
        signature, r_ellipsis = robjects.functions.map_signature(stf)


@pytest.mark.parametrize(
    'r_code,args,kwargs,expected',
    (
         ('function(x, y=1, z=2) {sum(x, y, z)}',
          (3, ), {}, 6),
         ('function(x, y=1, z=2) {sum(x, y, z)}',
          (3, 4), {}, 9),
         ('function(...) {sum(...)}',
          (3, 2, 4), {}, 9),
        ('function(x, ...) {sum(x, ...)}',
          (3, 2, 4), {}, 9),
        ('function(x, ..., z=1) {sum(x, ..., z)}',
          (3, 2, 4), {}, 10),
        ('function(x, ..., z=1) {sum(x, ..., z)}',
          (3, 2, 4), {'z': 2}, 11),
    )
)
def test_wrap_r_function_args(r_code, args, kwargs, expected):
    r_func = robjects.r(r_code)
    stf = robjects.functions.SignatureTranslatedFunction(r_func)
    w_func = robjects.functions.wrap_r_function(stf, 'foo')
    res = w_func(*args, **kwargs)
    assert tuple(res) == (expected, )


@pytest.mark.parametrize('is_method', (True, False))
def test_wrap_r_function(is_method):
    r_code = 'function(x, y=FALSE, z="abc") TRUE'
    parameter_names = ('self', 'x', 'y', 'z') if is_method else ('x', 'y', 'z')
    r_func = robjects.r(r_code)
    foo = robjects.functions.wrap_r_function(r_func, 'foo',
                                             is_method=is_method)
    assert inspect.getclosurevars(foo).nonlocals['r_func'].rid == r_func.rid
    assert tuple(foo.__signature__.parameters.keys()) == parameter_names
    if not is_method:
        res = foo(1)
        assert res[0] is True


@pytest.mark.parametrize('wrap_docstring',
                         (None, robjects.functions.wrap_docstring_default))
def test_wrap_r_function_docstrings(wrap_docstring):
    r_code = 'function(x, y=FALSE, z="abc") TRUE'
    r_func = robjects.r(r_code)
    foo = robjects.functions.wrap_r_function(r_func, 'foo', wrap_docstring=wrap_docstring)
    # TODO: only an integration test ? Nothing is tested.
