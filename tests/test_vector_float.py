import pytest
import rpy2.rinterface as ri

ri.initr()

def test_init_from_seq():
    seq = (1.0, 2.0, 3.0)
    v = ri.FloatSexpVector(seq)
    assert len(v) == 3
    for x,y in zip(seq, v):
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
