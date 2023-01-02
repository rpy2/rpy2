import array
import pytest
import struct
import sys
import rpy2.rinterface as ri

try:
    import numpy
    has_numpy = True
except ImportError:
    has_numpy = False

ri.initr()


def test_init_from_iter():
    seq = range(3)
    v = ri.IntSexpVector(seq)
    assert len(v) == 3
    for x, y in zip(seq, v):
        assert x == y


def test_init_from_seq_invalid_item():
    seq = (1, 'b', 3)
    with pytest.raises(ValueError):
        ri.IntSexpVector(seq)


@pytest.mark.skip(reason='WIP')
@pytest.mark.skipif(struct.calcsize('P') < 8,
                    reason='Only relevant on 64 architectures.')
def test_init_from_seq_invalid_overflow():
    MAX_INT = ri._rinterface._MAX_INT
    v = ri.IntSexpVector((MAX_INT, 42))
    assert v[0] == MAX_INT
    assert v[1] == 42
    # check 64-bit architecture
    with pytest.raises(OverflowError):
        ri.IntSexpVector((MAX_INT + 1, ))


def _test_from_int_memoryview():
    a = array.array('i', range(3, 103))
    mv = memoryview(a)
    vec = ri.IntSexpVector.from_memoryview(mv)
    assert tuple(range(3, 103)) == tuple(vec)


def test_from_long_memoryview():
    arrtype = 'l'
    if ri._rinterface.ffi.sizeof('int') == ri._rinterface.ffi.sizeof('long'):
        arrtype = 'q'
    a = array.array(arrtype, range(3, 103))
    mv = memoryview(a)
    with pytest.raises(ValueError):
        ri.IntSexpVector.from_memoryview(mv)


def test_from_intarray_object():
    a = array.array('l', range(3, 103))
    vec = ri.IntSexpVector.from_object(a)


def test_from_longarray_object():
    a = array.array('l', range(3, 103))
    vec = ri.IntSexpVector.from_object(a)
    assert tuple(range(3, 103)) == tuple(vec)


def test_from_tuple_object():
    a = tuple(range(3, 103))
    vec = ri.IntSexpVector.from_object(a)
    assert tuple(range(3, 103)) == tuple(vec)


def test_getitem():
    vec = ri.IntSexpVector(range(1, 10))
    assert vec[1] == 2


def test_setitem():
    vec = ri.IntSexpVector(range(1, 10))
    vec[1] = 100
    assert vec[1] == 100


def test_getslice():
    vec = ri.IntSexpVector([1, 2, 3])
    vec = vec[0:2]
    assert len(vec) == 2
    assert vec[0] == 1
    assert vec[1] == 2


def test_getslice_negative():
    vec = ri.IntSexpVector([1, 2, 3])
    vec_s = vec[-2:-1]
    assert len(vec_s) == 1
    assert vec_s[0] == 2


def test_setslice():
    vec = ri.IntSexpVector([1, 2, 3])
    vec[0:2] = ri.IntSexpVector([11, 12])
    assert len(vec) == 3
    assert vec[0] == 11
    assert vec[1] == 12


def test_setslice_negative():
    vec = ri.IntSexpVector([1, 2, 3])
    vec[-2:-1] = ri.IntSexpVector([33, ])
    assert len(vec) == 3
    assert vec[1] == 33


def test_index():
    x = ri.IntSexpVector((1, 2, 3))
    assert x.index(1) == 0
    assert x.index(3) == 2
    with pytest.raises(ValueError):
        x.index(33)
    with pytest.raises(ValueError):
        x.index('a')


def test_getitem_negative_outffbound():
    x = ri.IntSexpVector((1, 2, 3))
    with pytest.raises(IndexError):
        x.__getitem__(-100)


def test_getitem_outofbound():
    x = ri.IntSexpVector((1, 2, 3))
    with pytest.raises(IndexError):
        x.__getitem__(10)


def test_getitem_outofbound_overmaxsize():
    x = ri.IntSexpVector((1, 2, 3))
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


def test_setitem_outffbound():
    vec = ri.IntSexpVector(range(5))
    with pytest.raises(IndexError):
        vec.__setitem__(10, 6)


@pytest.mark.skipif(not has_numpy,
                    reason='numpy currently required for memoryview to work.')
def test_memoryview_2d():
    shape = (5, 2)
    values = tuple(range(10))
    # R arrays are column-major, therefore
    # a slice like [:, :] should look
    # like:
    #
    #  0  5
    #  1  6
    #  2  7
    #  3  8
    #  4  9

    rarray = ri.baseenv['array'](
        ri.IntSexpVector(values),
        dim=ri.IntSexpVector(shape))
    mv = rarray.memoryview()
    assert mv.f_contiguous is True
    assert mv.shape == shape
    assert mv.tolist() == [[0, 5],
                           [1, 6],
                           [2, 7],
                           [3, 8],
                           [4, 9]]
    rarray[0] = 10
    assert mv.tolist() == [[10, 5],
                           [1, 6],
                           [2, 7],
                           [3, 8],
                           [4, 9]]


@pytest.mark.skipif(not has_numpy,
                    reason='numpy currently required for memoryview to work.')
def test_memoryview_3d():
    shape = (5, 2, 3)
    values = tuple(range(30))
    # R arrays are column-major, therefore
    # a slice through the first index in the third dimension should look
    # like:
    #
    #  0  5
    #  1  6
    #  2  7
    #  3  8
    #  4  9

    rarray = ri.baseenv['array'](
        ri.IntSexpVector(values),
        dim=ri.IntSexpVector(shape))
    mv = rarray.memoryview()
    assert mv.f_contiguous is True
    assert mv.shape == shape
    assert tuple(x[0][0] for x in mv.tolist()) == (0, 1, 2, 3, 4)


def test_array_protocol():
    v = ri.IntSexpVector(range(10))
    ai = v.__array_interface__
    assert ai['version'] == 3
