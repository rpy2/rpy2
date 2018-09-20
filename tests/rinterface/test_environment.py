# coding: utf-8
import pytest
from .. import utils
import rpy2.rinterface as rinterface

rinterface.initr()


def _just_pass(x):
    pass


@pytest.fixture(scope='module')
def silent_console_print():
    with utils.obj_in_module(rinterface.callbacks, 'consolewrite_print', _just_pass):
        yield

        
def test_new():
    sexp = rinterface.globalenv
    sexp_new = rinterface.SexpEnvironment(sexp)

    assert sexp.rsame(sexp_new)

    sexp_new2 = rinterface.Sexp(sexp)
    assert sexp.rsame(sexp_new2)
    
    del(sexp)
    
    assert sexp_new.rsame(sexp_new2)

    with pytest.raises(ValueError):
        rinterface.SexpEnvironment('2')


#TODO: the next few tests should be moved to testing the
# cdata -> rinterface-object mapper
def test_globalenv():
    assert isinstance(rinterface.globalenv, rinterface.SexpEnvironment) 


def test_getclosure():
    help_R = rinterface.globalenv.get('help')
    assert isinstance(help_R, rinterface.SexpClosure)


def test_getvector():
    pi_R = rinterface.globalenv.get('pi')
    assert isinstance(pi_R, rinterface.SexpVector)


def test_getenvironment():
    ge_R = rinterface.globalenv.get(".GlobalEnv")
    assert isinstance(ge_R, rinterface.SexpEnvironment)


@pytest.mark.skip(reason='segfault')
def test_getonlyfromloadedlibrary():
    with pytest.raises(KeyError):
        rinterface.globalenv.get('survfit')
    try:
        rinterface.parse('library("survival")')
        sfit_R = rinterface.globalenv.get('survfit')
        assert isinstance(sfit_R, rinterface.SexpClosure)
    finally:
        rinterface.parse('detach("package:survival")')


@pytest.mark.skip(reason='segfault')
def test_get_functiononly_keyerror():
    # now with the function-only option
    with pytest.raises(KeyError):
        res = rinterface.globalenv.get('pi', wantfun=True)


def test_get_functiononly():
    hist = rinterface.globalenv.get('hist', wantfun=False)
    assert rinterface.RTYPES.CLOSXP == hist.typeof
    rinterface.globalenv['hist'] = rinterface.StrSexpVector(['foo', ])

    hist = rinterface.globalenv.get('hist', wantfun=True)
    assert rinterface.RTYPES.CLOSXP == hist.typeof


# TODO: isn't this already tested elsewhere ?
def test_subscript_emptystring():
    ge = rinterface.globalenv
    with pytest.raises(ValueError):
        res = ge['']


def test_subscript():
    ge = rinterface.globalenv
    obj = ge.get('letters')
    ge['a'] = obj
    a = ge['a']
    assert ge.get('identical')(obj, a)


def test_subscript_utf8():
    env = rinterface.baseenv['new.env']()
    env['呵呵'] = rinterface.IntSexpVector((1,))
    assert len(env) == 1
    assert len(env['呵呵']) == 1
    assert env['呵呵'][0] == 1


def test_subscript_missing_utf8():
    env = rinterface.baseenv['new.env']()
    with pytest.raises(KeyError), \
         pytest.warns(rinterface.RRuntimeWarning):
            env['呵呵']


def test_length():
    new_env = rinterface.globalenv.get('new.env')
    env = new_env()
    assert len(env) == 0
    env['a'] = rinterface.IntSexpVector([123, ])
    assert len(env) == 1
    env['b'] = rinterface.IntSexpVector([123, ])
    assert len(env) == 2


def test_iter():
    new_env = rinterface.globalenv.get('new.env')
    env = new_env()
    env['a'] = rinterface.IntSexpVector([123, ])
    env['b'] = rinterface.IntSexpVector([456, ])
    symbols = [x for x in env]
    assert len(symbols) == 2
    for s in ['a', 'b']:
        assert s in symbols


def test_keys():
    new_env = rinterface.globalenv.get('new.env')
    env = new_env()
    env['a'] = rinterface.IntSexpVector([123, ])
    env['b'] = rinterface.IntSexpVector([456, ])
    symbols = tuple(env.keys())
    assert len(symbols) == 2
    for s in ['a', 'b']:
        assert s in symbols


def test_del():
    env = rinterface.globalenv.get("new.env")()
    env['a'] = rinterface.IntSexpVector([123, ])
    env['b'] = rinterface.IntSexpVector([456, ])
    assert len(env) == 2
    del(env['a'])
    assert len(env) == 1
    assert 'b' in env


def test_del_keyerror():
    with pytest.raises(KeyError):
        rinterface.globalenv.__delitem__('foo')


def test_del_baseerror():
    with pytest.raises(ValueError):
        rinterface.baseenv.__delitem__('letters')
