import pytest
from rpy2 import robjects


def test_init():
    vec = robjects.FactorVector(robjects.StrVector('abaabc'))
    assert len(vec) == 6


def test_factor_repr():
    vec = robjects.vectors.FactorVector(('abc', 'def', 'ghi'))
    s = repr(vec)
    assert s.endswith('[abc, def, ghi]')

    
def test_isordered():
    vec = robjects.FactorVector(robjects.StrVector('abaabc'))
    assert vec.isordered is False


def test_nlevels():
    vec = robjects.FactorVector(robjects.StrVector('abaabc'))
    assert vec.nlevels == 3


def test_levels():
    vec = robjects.FactorVector(robjects.StrVector('abaabc'))
    assert len(vec.levels) == 3
    assert set(('a','b','c')) == set(tuple(vec.levels))


def test_levels_set():
    vec = robjects.FactorVector(robjects.StrVector('abaabc'))
    vec.levels = robjects.vectors.StrVector('def')
    assert set(('d','e','f')) == set(tuple(vec.levels))


def test_iter_labels():
    values = 'abaabc'
    vec = robjects.FactorVector(robjects.StrVector(values))
    it = vec.iter_labels()
    for a, b in zip(values, it):
        assert a == b


def test_factor_with_attrs():
    # issue #299
    r_src = """
    x <- factor(c("a","b","a"))
    attr(x, "foo") <- "bar"
    x
    """
    x = robjects.r(r_src)
    assert 'foo' in x.list_attrs()
