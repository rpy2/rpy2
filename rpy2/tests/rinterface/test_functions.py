# coding: utf-8
import pytest
import rpy2.rinterface as rinterface
import rpy2.rlike.container as rlc

rinterface.initr()


def _noconsole(x):
    pass


@pytest.fixture(scope='module')
def silent_consolewrite():
    module = rinterface.callbacks
    name = 'consolewrite_print'
    backup_func = getattr(module, name)
    setattr(module, name, _noconsole)
    try:
        yield
    finally:
        setattr(module, name, backup_func)


def test_new():
    x = 'a'
    with pytest.raises(ValueError):
        rinterface.SexpClosure(x)


def test_typeof():
    sexp = rinterface.globalenv.find('plot')
    assert sexp.typeof == rinterface.RTYPES.CLOSXP


def test_r_error():
    r_sum = rinterface.baseenv['sum']
    letters = rinterface.baseenv['letters']
    with pytest.raises(rinterface.embedded.RRuntimeError),\
            pytest.warns(rinterface.RRuntimeWarning):
        r_sum(letters)


def test_string_argument():
    r_nchar = rinterface.baseenv['::']('base', 'nchar')
    res = r_nchar('foo')
    assert res[0] == 3


def test_utf8_argument_name():
    c = rinterface.globalenv.find('c')
    d = dict([(u'哈哈', 1)])
    res = c(**d)
    assert u'哈哈' == res.do_slot('names')[0]


def test_emptystringparams():
    d = dict([('', 1)])
    with pytest.raises(ValueError):
        rinterface.baseenv['list'](**d)


def test_closureenv_isenv():
    exp = rinterface.parse('function() { }')
    fun = rinterface.baseenv['eval'](exp)
    assert isinstance(fun.closureenv, rinterface.SexpEnvironment)


def test_closureenv():

    assert 'y' not in rinterface.globalenv

    exp = rinterface.parse('function(x) { x[y] }')
    fun = rinterface.baseenv['eval'](exp)
    vec = rinterface.baseenv['letters']

    assert isinstance(fun.closureenv, rinterface.SexpEnvironment)

    with pytest.raises(rinterface.embedded.RRuntimeError):
        with pytest.warns(rinterface.RRuntimeWarning):
            fun(vec)

    fun.closureenv['y'] = (rinterface
                           .IntSexpVector([1, ]))
    assert 'a' == fun(vec)[0]

    fun.closureenv['y'] = (rinterface
                           .IntSexpVector([2, ]))
    assert 'b' == fun(vec)[0]


def test_call_s4_setClass():
    # R's package "methods" can perform uncommon operations
    r_setClass = rinterface.globalenv.find('setClass')
    r_representation = rinterface.globalenv.find('representation')
    attrnumeric = rinterface.StrSexpVector(['numeric', ])
    classname = rinterface.StrSexpVector(['Track', ])
    classrepr = r_representation(x=attrnumeric,
                                 y=attrnumeric)
    r_setClass(classname,
               classrepr)
    # TODO: where is the test ?


def test_call_OrdDict():
    ad = rlc.OrdDict((('a', rinterface.IntSexpVector([2, ])),
                      ('b', rinterface.IntSexpVector([1, ])),
                      (None, rinterface.IntSexpVector([5, ])),
                      ('c', rinterface.IntSexpVector([0, ]))))

    mylist = rinterface.baseenv['list'].rcall(tuple(ad.items()),
                                              rinterface.globalenv)

    names = [x for x in mylist.do_slot('names')]

    for i in range(4):
        assert ('a', 'b', '', 'c')[i] == names[i]


def test_call_OrdDictEnv():
    ad = rlc.OrdDict(((None, rinterface.parse('sum(x)')), ))
    env_a = rinterface.baseenv['new.env']()
    env_a['x'] = rinterface.IntSexpVector([1, 2, 3])
    sum_a = rinterface.baseenv['eval'].rcall(tuple(ad.items()), env_a)
    assert 6 == sum_a[0]
    env_b = rinterface.baseenv['new.env']()
    env_b['x'] = rinterface.IntSexpVector([4, 5, 6])
    sum_b = rinterface.baseenv['eval'].rcall(tuple(ad.items()), env_b)
    assert 15 == sum_b[0]


def test_error_in_call():
    r_sum = rinterface.baseenv['sum']

    with pytest.raises(rinterface.embedded.RRuntimeError),\
            pytest.warns(rinterface.RRuntimeWarning):
        r_sum(2, 'a')


def test_missing_arg():
    exp = rinterface.parse('function(x) { missing(x) }')
    fun = rinterface.baseenv['eval'](exp)
    nonmissing = rinterface.IntSexpVector([0, ])
    missing = rinterface.MissingArg
    assert not fun(nonmissing)[0]
    assert fun(missing)[0]


def test_scalar_convert_integer():
    assert 'integer' == rinterface.baseenv['typeof'](int(1))[0]


def test_scalar_convert_double():
    assert 'double' == rinterface.baseenv['typeof'](1.0)[0]


def test_scalar_convert_boolean():
    assert 'logical' == rinterface.baseenv['typeof'](True)[0]


@pytest.mark.parametrize('give_env', (True, False))
@pytest.mark.parametrize('use_rlock', (True, False))
def test_call_in_context(give_env, use_rlock):
    ls = rinterface.baseenv['ls']
    get = rinterface.baseenv['get']
    if give_env:
        env = rinterface.baseenv['new.env']()
    else:
        env = None
    assert 'foo' not in ls()
    with rinterface.local_context(env=env, use_rlock=use_rlock) as lc:
        lc['foo'] = 123
        assert tuple(get('foo')) == (123, )
    assert 'foo' not in ls()


@pytest.mark.parametrize('use_rlock', (True, False))
def test_call_in_context_nested(use_rlock):
    ls = rinterface.baseenv['ls']
    get = rinterface.baseenv['get']
    assert 'foo' not in ls()
    with rinterface.local_context() as lc_a:
        lc_a['foo'] = 123
        assert tuple(get('foo')) == (123, )
        with rinterface.local_context(use_rlock=use_rlock) as lc_b:
            lc_b['foo'] = 456
            assert tuple(get('foo')) == (456, )
        assert tuple(get('foo')) == (123, )
    assert 'foo' not in ls()
