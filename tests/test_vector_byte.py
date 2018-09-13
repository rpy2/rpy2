import pytest
import rpy2.rinterface as ri

ri.initr()


def test_init_from_bytes():
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


def test_getitem():
    vec = ri.ByteSexpVector((b'a', b'b', b'c'))
    assert vec[1] == ord(b'b')

    
def test_setitem():
    vec = ri.ByteSexpVector((b'a', b'b', b'c'))
    vec[1] = b'z'
    assert vec[1] == ord(b'z')
