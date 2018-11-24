import pytest
import rpy2.rinterface as ri

ri.initr()


def test_init_from_seqr():
    seq = [1+2j, 5+7j, 0+1j]
    v = ri.ComplexSexpVector(seq)
    assert len(v) == 3
    for x, y in zip(seq, v):
        assert x == y


def test_init_from_seq_invalid_item():
    seq = [1+2j, 'a', 0+1j]
    with pytest.raises(TypeError):
        ri.ComplexSexpVector(seq)


def test_getitem():
    vec = ri.ComplexSexpVector([1+2j, 5+7j, 0+1j])
    assert vec[1] == 5+7j


def test_setitem():
    vec = ri.ComplexSexpVector([1+2j, 5+7j, 0+1j])
    vec[1] = 100+3j
    assert vec[1] == 100+3j


def test_getslice():
    vec = ri.ComplexSexpVector([1+2j, 5+7j, 0+1j])
    vec_s = vec[0:2]
    assert len(vec_s) == 2
    assert vec_s[0] == 1+2j
    assert vec_s[1] == 5+7j


def test_getslice_negative():
    vec = ri.ComplexSexpVector([1+2j, 5+7j, 0+1j])
    vec_s = vec[-2:-1]
    assert len(vec_s) == 1
    assert vec_s[0] == 5+7j


def test_setslice():
    vec = ri.ComplexSexpVector([1+2j, 5+7j, 0+1j])
    vec[0:2] = ri.ComplexSexpVector([100+3j, 5-5j])
    assert len(vec) == 3
    assert vec[0] == 100+3j
    assert vec[1] == 5-5j


def test_setslice_negative():
    vec = ri.ComplexSexpVector([1+2j, 5+7j, 0+1j])
    vec[-2:-1] = ri.ComplexSexpVector([100+3j, ])
    assert len(vec) == 3
    assert vec[1] == 100+3j


def test_index():
    vec = ri.ComplexSexpVector([1+2j, 5+7j, 0+1j])
    assert vec.index(5+7j) == 1
    assert vec.index(0+1j) == 2
    with pytest.raises(ValueError):
        vec.index(2)
    with pytest.raises(ValueError):
        vec.index('a')
