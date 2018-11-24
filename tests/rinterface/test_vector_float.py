import pytest
import rpy2.rinterface as ri

ri.initr()


def test_init_from_seq():
    seq = (1.0, 2.0, 3.0)
    v = ri.FloatSexpVector(seq)
    assert len(v) == 3
    for x, y in zip(seq, v):
        assert x == y


def test_init_from_iter():
    it = range(3)
    v = ri.FloatSexpVector(it)
    assert len(v) == 3
    for x, y in zip(range(3), v):
        assert x == y


def test_init_From_seq_invalid_float():
    seq = (1.0, 'b', 3.0)
    with pytest.raises(ValueError):
        ri.FloatSexpVector(seq)


def test_getitem():
    vec = ri.FloatSexpVector([1.0, 2.0, 3.0])
    assert vec[1] == 2.0


def test_setitem():
    vec = ri.FloatSexpVector([1.0, 2.0, 3.0])
    vec[1] = 100.0
    assert vec[1] == 100.0


def test_getslice():
    vec = ri.FloatSexpVector([1.0, 2.0, 3.0])
    vec = vec[0:2]
    assert len(vec) == 2
    assert vec[0] == 1.0
    assert vec[1] == 2.0


def test_setslice():
    vec = ri.FloatSexpVector([1.0, 2.0, 3.0])
    vec[0:2] = ri.FloatSexpVector([11.0, 12.0])
    assert len(vec) == 3
    assert vec[0] == 11.0
    assert vec[1] == 12.0
    assert vec[2] == 3.0
