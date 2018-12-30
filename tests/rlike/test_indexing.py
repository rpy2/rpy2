import pytest
import rpy2.rlike.indexing as rfi


def test_order():
    seq  = (2, 1, 5, 3, 4)
    expected = (1, 2, 3, 4, 5)
    res = rfi.order(seq)
    for va, vb in zip(expected, res):
        assert seq[vb] == va
