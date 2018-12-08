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
    keys = list(env.keys())
    assert len(keys) == 1
    keys.sort()
    for it_a, it_b in zip(keys,
                          ('a',)):
        assert it_a == it_b


def test_items():
    env = robjects.Environment()
    env['a'] = 123
    items = list(env.items())
    assert len(items) == 1
    items.sort(key=lambda x: x[0])
    for it_a, it_b in zip(items,
                          (('a', 123),)):
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
        robjs.append(env.pop('c'))
    assert env.pop('c', 789) == 789
        

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
