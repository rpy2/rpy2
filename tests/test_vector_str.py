import pytest
import struct
import rpy2.rinterface as ri

ri.initr()


def test_init_from_seqr():
    seq = ['foo', 'bar', 'baz']
    v = ri.StrSexpVector(seq)
    assert len(v) == 3
    for x,y in zip(seq, v):
        assert x == y


def test_init_from_seq_invalid_item():
    seq = ['foo', 0, 'baz']
    with pytest.raises(ValueError):
        ri.StrSexpVector(seq)


def test_getitem():
    vec = ri.StrSexpVector(['foo', 'bar', 'baz'])
    assert vec[1] == 'bar'

    
def test_setitem():
    vec = ri.StrSexpVector(['foo', 'bar', 'baz'])
    vec[1] = 'boo'
    assert vec[1] == 'boo'


def test_getslice():
    vec = ri.StrSexpVector(['foo', 'bar', 'baz'])
    vec_s = vec[0:2]
    assert len(vec_s) == 2
    assert vec_s[0] == 'foo'
    assert vec_s[1] == 'bar'

    
def test_getslice_negative():
    vec = ri.StrSexpVector(['foo', 'bar', 'baz'])
    vec_s = vec[-2:-1]
    assert len(vec_s) == 1
    assert vec_s[0] == 'bar'


def test_setslice():
    vec = ri.StrSexpVector(['foo', 'bar', 'baz'])
    vec[0:2] = ri.StrSexpVector(['boo', 'noo'])
    assert len(vec) == 3
    assert vec[0] == 'boo'
    assert vec[1] == 'noo'


def test_setslice_negative():
    vec = ri.StrSexpVector(['foo', 'bar', 'baz'])
    vec[-2:-1] = ri.StrSexpVector(['boo',])
    assert len(vec) == 3
    assert vec[1] == 'boo'


def test_index():
    vec = ri.StrSexpVector(['foo', 'bar', 'baz'])
    assert vec.index('bar') == 1
    assert vec.index('baz') == 2
    with pytest.raises(ValueError):
        vec.index(2)
    with pytest.raises(ValueError):
        vec.index('a')
