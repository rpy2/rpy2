import array
import pytest
import rpy2.rinterface as ri

ri.initr()


def test_init_from_bytes_in_seq():
    seq = (b'a', b'b', b'c')
    v = ri.ByteSexpVector(seq)
    assert len(v) == 3
    for x, y in zip(seq, v):
        assert ord(x) == y


def test_init_from_seq_of_bytes():
    seq = (b'a', b'b', b'c')
    v = ri.ByteSexpVector(seq)
    assert len(v) == 3
    for x, y in zip(seq, v):
        assert ord(x) == y


def test_init_from_bytes():
    seq = b'abc'
    v = ri.ByteSexpVector(seq)
    assert len(v) == 3
    for x, y in zip(seq, v):
        assert x == y


def test_init_from_seq_invalid_byte():
    seq = (b'a', [], b'c')
    with pytest.raises(ValueError):
        ri.ByteSexpVector(seq)


def test_from_memoryview():
    a = array.array('b', b'abcdefg')
    mv = memoryview(a)
    vec = ri.ByteSexpVector.from_memoryview(mv)
    assert tuple(b'abcdefg') == tuple(vec)


def test_getitem():
    vec = ri.ByteSexpVector((b'a', b'b', b'c'))
    assert vec[1] == ord(b'b')


def test_getitem_slice():
    vec = ri.ByteSexpVector((b'a', b'b', b'c'))
    assert tuple(vec[:2]) == (ord(b'a'), ord(b'b'))


def test_setitem():
    vec = ri.ByteSexpVector((b'a', b'b', b'c'))
    vec[1] = b'z'
    assert vec[1] == ord(b'z')


def test_setitem_int():
    vec = ri.ByteSexpVector((b'a', b'b', b'c'))
    vec[1] = ord(b'z')
    assert vec[1] == ord(b'z')


def test_setitem_int_invalid():
    vec = ri.ByteSexpVector((b'a', b'b', b'c'))
    with pytest.raises(ValueError):
        vec[1] = 333


def test_setitem_slice():
    values = (b'a', b'b', b'c')
    vec = ri.ByteSexpVector(values)
    vec[:2] = b'yz'
    assert tuple(vec) == tuple(b'yzc')


def test_setitem_slice_invalid():
    values = (b'a', b'b', b'c')
    vec = ri.ByteSexpVector(values)
    with pytest.raises(TypeError):
        vec['foo'] = (333, ord(b'z'))

    with pytest.raises(ValueError):
        vec[:2] = (333, ord(b'z'))
