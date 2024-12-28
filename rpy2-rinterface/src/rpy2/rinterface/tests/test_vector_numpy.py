import pytest
import rpy2.rinterface as rinterface

try:
    import numpy
    has_numpy = True
except ImportError:
    has_numpy = False

rinterface.initr()


def floatEqual(x, y, epsilon=0.00000001):
    return abs(x - y) < epsilon


@pytest.mark.skipif(not has_numpy, reason='Package numpy is not installed.')
def test_array_struct_int():
    px = [1, -2, 3]
    x = rinterface.IntSexpVector(px)
    nx = numpy.asarray(x.memoryview())
    assert nx.dtype.kind == 'i'
    for orig, new in zip(px, nx):
        assert orig == new

    # change value in the Python array... makes it change in the R vector
    nx[1] = 12
    assert x[1] == 12


@pytest.mark.skipif(not has_numpy, reason='Package numpy is not installed.')
def test_array_struct_double():
    px = [1.0, -2.0, 3.0]
    x = rinterface.FloatSexpVector(px)
    nx = numpy.asarray(x.memoryview())
    assert nx.dtype.kind == 'f'
    for orig, new in zip(px, nx):
        assert orig == new

    # change value in the Python array... makes it change in the R vector
    nx[1] = 333.2
    assert x[1] == 333.2


@pytest.mark.skip(reason='WIP')
@pytest.mark.skipif(not has_numpy, reason='Package numpy is not installed.')
def test_array_struct_complex():
    px = [1+2j, 2+5j, -1+0j]
    x = rinterface.ComplexSexpVector(px)
    nx = numpy.asarray(x.memoryview())
    assert nx.dtype.kind == 'c'
    for orig, new in zip(px, nx):
        assert orig == new


@pytest.mark.skipif(not has_numpy, reason='Package numpy is not installed.')
def test_array_struct_boolean():
    px = [True, False, True]
    x = rinterface.BoolSexpVector(px)
    nx = numpy.asarray(x.memoryview())
    # not 'b' as R boolean vectors are array of ints.
    assert nx.dtype.kind == 'i'
    for orig, new in zip(px, nx):
        assert orig == new


@pytest.mark.skipif(not has_numpy, reason='Package numpy is not installed.')
def test_array_shape_len3():
    extract = rinterface.baseenv['[']
    rarray = rinterface.baseenv['array'](
        rinterface.IntSexpVector(range(30)),
        dim=rinterface.IntSexpVector([5, 2, 3]))
    npyarray = numpy.array(rarray.memoryview())
    for i in range(5):
        for j in range(2):
            for k in range(3):
                assert extract(rarray, i+1, j+1, k+1)[0] == npyarray[i, j, k]
