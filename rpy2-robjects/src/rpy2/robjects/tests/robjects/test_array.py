import pytest
import rpy2.rinterface as rinterface
import rpy2.robjects as robjects
import array


# TODO: move to common module for testing
def almost_equal(x, y, epsilon = 0.00001):
    return abs(y - x) <= epsilon


def test_init_invalid():
    with pytest.raises(TypeError):
        robjects.vectors.IntArray(3)


def test_init():
    m = rinterface.globalenv.find('matrix')(1, nrow=5, ncol=3)
    a = robjects.vectors.FloatArray(m)
    if int(rinterface.sexp.RVersion()['major']) >= 4:
        expected = ('matrix', 'array')
    else:
        expected = ('matrix', )
    assert tuple(a.rclass) == expected


def test_dim():
    m = robjects.r.matrix(1, nrow=5, ncol=3)
    a = robjects.vectors.FloatArray(m)
    assert len(a.dim) == 2
    assert tuple(a.dim) == (5, 3)


def test_dim_set():
    m = robjects.r.matrix(1, nrow=5, ncol=3)
    a = robjects.vectors.FloatArray(m)
    a.dim = robjects.vectors.IntVector([3, 5])
    assert len(a.dim) == 2
    assert tuple(a.dim) == (3, 5)


def test_dim_set_null():
    m = robjects.r.matrix(1, nrow=5, ncol=3)
    a = robjects.vectors.FloatArray(m)
    a.dim = robjects.NULL
    assert a.dim == robjects.NULL


def test_dim_set_invalid():
    m = robjects.r.matrix(1, nrow=5, ncol=3)
    a = robjects.vectors.FloatArray(m)
    with pytest.raises(TypeError):
        a.dim = [5, 3]


def test_dim_set_invalid2():
    m = robjects.r.matrix(1, nrow=5, ncol=3)
    a = robjects.vectors.FloatArray(m)
    with pytest.raises(ValueError):
        a.dim = robjects.vectors.IntVector([5, 5])


def test_names_get():
    dimnames = robjects.r.list(robjects.StrVector(['a', 'b', 'c']),
                               robjects.StrVector(['d', 'e']))
    m = robjects.r.matrix(1, nrow=3, ncol=2,
                          dimnames = dimnames)
    a = robjects.vectors.FloatArray(m)
    res = a.names
    r_identical = robjects.r.identical
    assert r_identical(dimnames[0], res[0])[0]
    assert r_identical(dimnames[1], res[1])[0]


def test_names_set():
    dimnames = robjects.r.list(robjects.StrVector(['a', 'b', 'c']),
                               robjects.StrVector(['d', 'e']))
    m = robjects.r.matrix(1, nrow=3, ncol=2)
    a = robjects.vectors.FloatArray(m)
    a.names = dimnames
    res = a.names
    r_identical = robjects.r.identical
    assert r_identical(dimnames[0], res[0])[0]
    assert r_identical(dimnames[1], res[1])[0]


# Test Matrix

def test_nrow_get():
    m = robjects.r.matrix(robjects.IntVector(range(6)), nrow=3, ncol=2)
    assert m.nrow == 3


def test_ncol_get():
    m = robjects.r.matrix(robjects.IntVector(range(6)), nrow=3, ncol=2)
    assert m.ncol == 2


def test_transpose():
    m = robjects.r.matrix(robjects.IntVector(range(6)),
                          nrow=3, ncol=2)
    mt = m.transpose()
    for i,val in enumerate((0,1,2,3,4,5,)):
        assert m[i] == val
    for i,val in enumerate((0,3,1,4,2,5)):
        assert mt[i] == val


def test_matmul():
    # 1 3
    # 2 4
    m = robjects.r.matrix(robjects.IntVector(range(1, 5)), nrow=2)
    # 1*1+3*2 1*3+3*4
    # 2*1+4*2 2*3+4*4
    m2 = m @ m
    for i,val in enumerate((7.0, 10.0, 15.0, 22.0,)):
        assert m2[i] == val


def test_crossprod():
    m = robjects.r.matrix(robjects.IntVector(range(4)), nrow=2)
    mcp = m.crossprod(m)
    for i,val in enumerate((1.0,3.0,3.0,13.0,)):
        assert mcp[i] == val


def test_tcrossprod():
    m = robjects.r.matrix(robjects.IntVector(range(4)), nrow=2)
    mtcp = m.tcrossprod(m)
    for i,val in enumerate((4,6,6,10,)):
        assert mtcp[i] == val


def test_svd():
    m = robjects.r.matrix(robjects.IntVector((1, -1, -1, 1)), nrow=2)
    res = m.svd()
    for i,val in enumerate(res.rx2("d")):
        assert almost_equal((2, 0)[i], val)


def test_eigen():
    m = robjects.r.matrix(robjects.IntVector((1, -1, -1, 1)), nrow=2)
    res = m.eigen()
    for i, val in enumerate(res.rx2("values")):
        assert (2, 0)[i] == val


def test_dot():
    m = robjects.r.matrix(robjects.IntVector(range(4)), nrow=2, ncol=2)
    m2 = m.dot(m)
    assert tuple(m2) == (2,3,6,11)


def test_colnames():
    m = robjects.r.matrix(robjects.IntVector(range(4)), nrow=2, ncol=2)
    assert m.colnames == rinterface.NULL
    m.colnames = robjects.StrVector(('a', 'b'))
    assert len(m.colnames) == 2
    assert m.colnames[0] == 'a'
    assert m.colnames[1] == 'b'    
    with pytest.raises(ValueError):
        m.colnames = robjects.StrVector(('a', 'b', 'c'))


def test_rownames():
    m = robjects.r.matrix(robjects.IntVector(range(4)), nrow=2, ncol=2)
    assert m.rownames == rinterface.NULL
    m.rownames = robjects.StrVector(('c', 'd'))
    assert len(m.rownames) == 2
    assert m.rownames[0] == 'c'
    assert m.rownames[1] == 'd'
    with pytest.raises(ValueError):
        m.rownames = robjects.StrVector(('a', 'b', 'c'))

