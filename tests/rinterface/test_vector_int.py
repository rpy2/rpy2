import pytest
import struct
import sys
import rpy2.rinterface as ri

ri.initr()


def test_init_from_iter():
    seq = range(3)
    v = ri.IntSexpVector(seq)
    assert len(v) == 3
    for x,y in zip(seq, v):
        assert x == y


def test_init_from_seq_invalid_item():
    seq = (1, 'b', 3)
    with pytest.raises(ValueError):
        ri.IntSexpVector(seq)


@pytest.mark.skipif(struct.calcsize('P') < 8,
                    reason='Only relevant on 64 architectures.')
def test_init_from_seq_invalid_overflow():
    MAX_INT = ri._rinterface._MAX_INT
    v = ri.IntSexpVector((MAX_INT - 1, MAX_INT))
    assert v[0] == MAX_INT - 1
    assert v[1] == MAX_INT
    # check 64-bit architecture
    with pytest.raises(OverflowError): 
        ri.IntSexpVector((MAX_INT + 1, ))


def test_getitem():
    vec = ri.IntSexpVector(range(1, 10))
    assert vec[1] == 2

    
def test_setitem():
    vec = ri.IntSexpVector(range(1, 10))
    vec[1] = 100
    assert vec[1] == 100


def test_getslice():
    vec = ri.IntSexpVector([1,2,3])
    vec = vec[0:2]
    assert len(vec) == 2
    assert vec[0] == 1
    assert vec[1] == 2

    
def test_getslice_negative():
    vec = ri.IntSexpVector([1,2,3])
    vec_s = vec[-2:-1]
    assert len(vec_s) == 1
    assert vec_s[0] == 2


def test_setslice():
    vec = ri.IntSexpVector([1,2,3])
    vec[0:2] = ri.IntSexpVector([11,12])
    assert len(vec) == 3
    assert vec[0] == 11
    assert vec[1] == 12


def test_setslice_negative():
    vec = ri.IntSexpVector([1,2,3])
    vec[-2:-1] = ri.IntSexpVector([33,])
    assert len(vec) == 3
    assert vec[1] == 33


def test_index():
    x = ri.IntSexpVector((1,2,3))
    assert x.index(1) == 0
    assert x.index(3) == 2
    with pytest.raises(ValueError):
        x.index(33)
    with pytest.raises(ValueError):
        x.index('a')


def test_getitem_negative_outffbound():
    x = ri.IntSexpVector((1,2,3))
    with pytest.raises(IndexError):
        x.__getitem__(-100)


def test_getitem_outofbound():
    x = ri.IntSexpVector((1,2,3))
    with pytest.raises(IndexError):
        x.__getitem__(10)

        
def test_getitem_outofbound():
    x = ri.IntSexpVector((1,2,3))
    with pytest.raises(IndexError):
        x.__getitem__(sys.maxsize + 1)


def test_getslice_missingboundary():
    vec = ri.IntSexpVector(range(1, 11))
    vec_slice = vec[:2]
    assert len(vec_slice) == 2
    assert vec_slice[0] == 1
    assert vec_slice[1] == 2
    vec_slice = vec[8:]
    assert len(vec_slice) == 2
    assert vec_slice[0] == 9
    assert vec_slice[1] == 10
    vec_slice = vec[-2:]
    assert len(vec_slice) == 2
    assert vec_slice[0] == 9
    assert vec_slice[1] == 10

    
def testAssignItemOutOfBound():
    vec = ri.IntSexpVector(range(5))
    with pytest.raises(IndexError):
        vec.__setitem__(10, 6)
