# coding: utf-8
import pytest
from .. import utils
import rpy2.rinterface as rinterface

rinterface.initr()


def _just_pass(x):
    pass


@pytest.fixture(scope='module')
def silent_console_print():
    with utils.obj_in_module(rinterface.callbacks,
                             'consolewrite_print', _just_pass):
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


# TODO: the next few tests should be moved to testing the
# cdata -> rinterface-object mapper
def test_globalenv():
    assert isinstance(rinterface.globalenv, rinterface.SexpEnvironment)


def test_getitem():
    with pytest.raises(KeyError):
        rinterface.globalenv['help']
    assert isinstance(rinterface.globalenv.find('help'), rinterface.Sexp)


def test_getitem_invalid():
    env = rinterface.baseenv["new.env"]()
    with pytest.raises(TypeError):
        env[None]
    with pytest.raises(ValueError):
        env['']


def test_setitem_invalid():
    env = rinterface.baseenv["new.env"]()
    with pytest.raises(TypeError):
        env[None] = 0
    with pytest.raises(ValueError):
        env[''] = 0


def test_setitem_baseenv_invalid():
    with pytest.raises(ValueError):
        rinterface.baseenv['pi'] = 42


def test_frame():
    env = rinterface.baseenv["new.env"]()
    f = env.frame()
    # Outside of an R call stack a frame will be NULL,
    # or so I understand.
    assert f is rinterface.NULL


def test_find_invalid_notstring():
    with pytest.raises(TypeError):
        rinterface.globalenv.find(None)


def test_find_invalid_empty():
    with pytest.raises(ValueError):
        rinterface.globalenv.find('')


def test_find_invalid_notfound():
    with pytest.raises(KeyError):
        rinterface.globalenv.find('asdf')


def test_find_closure():
    help_R = rinterface.globalenv.find('help')
    assert isinstance(help_R, rinterface.SexpClosure)


def test_find_vector():
    pi_R = rinterface.globalenv.find('pi')
    assert isinstance(pi_R, rinterface.SexpVector)


def test_find_environment():
    ge_R = rinterface.globalenv.find(".GlobalEnv")
    assert isinstance(ge_R, rinterface.SexpEnvironment)


def test_find_onlyfromloadedlibrary():
    with pytest.raises(KeyError):
        rinterface.globalenv.find('survfit')
    try:
        rinterface.evalr('library("survival")')
        sfit_R = rinterface.globalenv.find('survfit')
        assert isinstance(sfit_R, rinterface.SexpClosure)
    finally:
        rinterface.evalr('detach("package:survival")')


def test_find_functiononly_keyerror():
    # now with the function-only option
    with pytest.raises(KeyError):
        rinterface.globalenv.find('pi', wantfun=True)


def test_find_functiononly():
    hist = rinterface.globalenv.find('hist', wantfun=False)
    assert rinterface.RTYPES.CLOSXP == hist.typeof
    rinterface.globalenv['hist'] = rinterface.StrSexpVector(['foo', ])

    with pytest.raises(KeyError):
        rinterface.globalenv.find('hist', wantfun=True)


# TODO: isn't this already tested elsewhere ?
def test_subscript_emptystring():
    ge = rinterface.globalenv
    with pytest.raises(ValueError):
        ge['']


def test_subscript():
    ge = rinterface.globalenv
    obj = ge.find('letters')
    ge['a'] = obj
    a = ge['a']
    assert ge.find('identical')(obj, a)


def test_subscript_utf8():
    env = rinterface.baseenv['new.env']()
    env['呵呵'] = rinterface.IntSexpVector((1,))
    assert len(env) == 1
    assert len(env['呵呵']) == 1
    assert env['呵呵'][0] == 1


def test_subscript_missing_utf8():
    env = rinterface.baseenv['new.env']()
    with pytest.raises(KeyError),\
            pytest.warns(rinterface.RRuntimeWarning):
        env['呵呵']


def test_length():
    new_env = rinterface.globalenv.find('new.env')
    env = new_env()
    assert len(env) == 0
    env['a'] = rinterface.IntSexpVector([123, ])
    assert len(env) == 1
    env['b'] = rinterface.IntSexpVector([123, ])
    assert len(env) == 2


def test_iter():
    new_env = rinterface.globalenv.find('new.env')
    env = new_env()
    env['a'] = rinterface.IntSexpVector([123, ])
    env['b'] = rinterface.IntSexpVector([456, ])
    symbols = [x for x in env]
    assert len(symbols) == 2
    for s in ['a', 'b']:
        assert s in symbols


def test_keys():
    new_env = rinterface.globalenv.find('new.env')
    env = new_env()
    env['a'] = rinterface.IntSexpVector([123, ])
    env['b'] = rinterface.IntSexpVector([456, ])
    symbols = tuple(env.keys())
    assert len(symbols) == 2
    for s in ['a', 'b']:
        assert s in symbols


def test_del():
    env = rinterface.globalenv.find("new.env")()
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


def test_enclos_get():
    assert isinstance(rinterface.baseenv.enclos, rinterface.SexpEnvironment)
    env = rinterface.baseenv["new.env"]()
    assert isinstance(env.enclos, rinterface.SexpEnvironment)


def test_enclos_baseenv_set():
    env = rinterface.baseenv["new.env"]()
    orig_enclosing_env = rinterface.baseenv.enclos
    enclosing_env = rinterface.baseenv["new.env"]()
    env.enclos = enclosing_env
    assert isinstance(env.enclos, rinterface.SexpEnvironment)
    assert enclosing_env != env.enclos


def test_enclos_baseenv_set_invalid():
    with pytest.raises(AssertionError):
        rinterface.baseenv.enclos = 123
