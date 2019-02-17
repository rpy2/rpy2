import array
import pytest
import rpy2.rinterface as ri

ri.initr()


def test_init_from_seqr():
    seq = [True, False, False]
    v = ri.BoolSexpVector(seq)
    assert len(v) == 3
    for x, y in zip(seq, v):
        assert x == y


def test_from_int_memoryview():
    a = array.array('i', (True, False, True))
    mv = memoryview(a)
    vec = ri.BoolSexpVector.from_memoryview(mv)
    assert (True, False, True) == tuple(vec)


def test_from_bool_memoryview():
    a = array.array('b', (True, False, True))
    mv = memoryview(a)
    with pytest.raises(ValueError):
        ri.BoolSexpVector.from_memoryview(mv)


def test_getitem():
    vec = ri.BoolSexpVector([True, False, False])
    assert vec[1] is False


def test_setitem():
    vec = ri.BoolSexpVector([True, False, False])
    vec[1] = True
    assert vec[1] is True


def test_getslice():
    vec = ri.BoolSexpVector([True, False, False])
    vec = vec[0:2]
    assert len(vec) == 2
    assert vec[0] is True
    assert vec[1] is False


def test_getslice_negative():
    vec = ri.BoolSexpVector([True, False, True])
    vec_s = vec[-2:-1]
    assert len(vec_s) == 1
    assert vec_s[0] is False


def test_setslice():
    vec = ri.BoolSexpVector([True, False, False])
    vec[0:2] = [True, True]
    assert len(vec) == 3
    assert vec[0] is True
    assert vec[1] is True


def test_setslice_negative():
    vec = ri.BoolSexpVector([True, False, False])
    vec[-2:-1] = ri.BoolSexpVector([True, ])
    assert len(vec) == 3
    assert vec[1] is True


def test_index():
    x = ri.BoolSexpVector((True, False, False))
    assert x.index(True) == 0
    assert x.index(False) == 1
    with pytest.raises(ValueError):
        x.index(2)
    with pytest.raises(ValueError):
        x.index('a')
