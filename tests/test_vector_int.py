import pytest
import struct
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
    v = ri.IntSexpVector((ri.R_LEN_T_MAX-1, ri.R_LEN_T_MAX))
    assert v[0] == ri.R_LEN_T_MAX-1
    assert v[1] == ri.R_LEN_T_MAX
    # check 64-bit architecture
    with pytest.raises(OverflowError): 
        ri.IntSexpVector((ri.R_LEN_T_MAX+1, ))

