import pytest
import rpy2.robjects as robjects
rinterface = robjects.rinterface
import array


def test_init_empty():
    env = robjects.Environment()
    assert env.typeof == rinterface.RTYPES.ENVSXP


def test_init_invalid():
    with pytest.raises(ValueError):
        robjects.Environment('a')

        
def test_getsetitem():
    env = robjects.Environment()
    env['a'] = 123
    assert 'a' in env
    a = env['a']
    assert len(a) == 1
    assert a[0] == 123


def test_keys():
    env = robjects.Environment()
    env['a'] = 123
    env['b'] = 234
    keys = list(env.keys())
    assert len(keys) == 2
    keys.sort()
    for it_a, it_b in zip(keys,
                          ('a', 'b')):
        assert it_a == it_b


def test_values():
    env = robjects.Environment()
    env['a'] = 123
    env['b'] = 234
    values = list(env.values())
    assert len(values) == 2
    values.sort(key=lambda x: x[0])
    for it_a, it_b in zip(values,
                          (123, 234)):
        assert len(it_a) == 1
        assert it_a[0] == it_b


def test_items():
    env = robjects.Environment()
    env['a'] = 123
    env['b'] = 234
    items = list(env.items())
    assert len(items) == 2
    items.sort(key=lambda x: x[0])
    for it_a, it_b in zip(items,
                          (('a', 123),
                           ('b', 234))):
        assert it_a[0] == it_b[0]
        assert it_a[1][0] == it_b[1]


def test_pop_key():
    env = robjects.Environment()
    env['a'] = 123
    env['b'] = 456
    robjs = []
    assert len(env) == 2
    robjs.append(env.pop('a'))
    assert len(env) == 1
    robjs.append(env.pop('b'))
    assert len(env) == 0
    assert [x[0] for x in robjs] == [123, 456]
    with pytest.raises(KeyError):
        env.pop('c')
    assert env.pop('c', 789) == 789
    with pytest.raises(ValueError):
        env.pop('c', 1, 2)


def test_popitem():
    env = robjects.Environment()
    env['a'] = 123
    env['b'] = 456
    robjs = []
    assert len(env) == 2
    robjs.append(env.popitem())
    assert len(env) == 1
    robjs.append(env.popitem())
    assert len(env) == 0
    assert sorted([(k, v[0]) for k, v in robjs]) == [('a', 123), ('b', 456)]

    with pytest.raises(KeyError):
        robjs.append(env.popitem())


def test_clear():
    env = robjects.Environment()
    env['a'] = 123
    env['b'] = 234
    assert len(env) == 2
    env.clear()
    assert len(env) == 0


@pytest.mark.parametrize('use_rlock', (True, False))
def test_call_in_context_nested(use_rlock):
    ls = robjects.baseenv['ls']
    get = robjects.baseenv['get']
    assert 'foo' not in ls()
    with robjects.environments.local_context() as lc_a:
        lc_a['foo'] = 123
        assert tuple(get('foo')) == (123, )
        with robjects.environments.local_context(use_rlock=use_rlock) as lc_b:
            lc_b['foo'] = 456
            assert tuple(get('foo')) == (456, )
        assert tuple(get('foo')) == (123, )
    assert 'foo' not in ls()
