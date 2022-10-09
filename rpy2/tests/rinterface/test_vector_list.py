import pytest
import operator
from .. import utils
import rpy2.rinterface as ri

ri.initr()


def test_init_from_seq():
    seq = (ri.FloatSexpVector([1.0]),
           ri.IntSexpVector([2, 3]),
           ri.StrSexpVector(['foo', 'bar']))
    v = ri.ListSexpVector(seq)
    assert len(v) == 3
    for x, y in zip(seq, v):
        utils.assert_equal_sequence(x, y)


def test_init_From_seq_invalid_elt():
    seq = (ri.FloatSexpVector([1.0]),
           lambda x: x,
           ri.StrSexpVector(['foo', 'bar']))
    with pytest.raises(Exception):
        ri.ListSexpVector(seq)


def test_getitem():
    seq = (ri.FloatSexpVector([1.0]),
           ri.IntSexpVector([2, 3]),
           ri.StrSexpVector(['foo', 'bar']))
    vec = ri.ListSexpVector(seq)
    utils.assert_equal_sequence(vec[1], ri.IntSexpVector([2, 3]))
    with pytest.raises(TypeError):
        vec[(2, 3)]


@pytest.mark.parametrize(
    'value_constructor,value_param,equal_func',
    ((ri.BoolSexpVector, [True, True, False], utils.assert_equal_sequence),
     (int, 9, operator.eq))
)
def test_setitem(value_constructor, value_param, equal_func):
    seq = (ri.FloatSexpVector([1.0]),
           ri.IntSexpVector([2, 3]),
           ri.StrSexpVector(['foo', 'bar']))
    vec = ri.ListSexpVector(seq)
    value = value_constructor(value_param)
    vec[1] = value
    equal_func(vec[1], value)
    with pytest.raises(TypeError):
        vec[(2, 3)] = 123


def test_getslice():
    seq = (ri.FloatSexpVector([1.0]),
           ri.IntSexpVector([2, 3]),
           ri.StrSexpVector(['foo', 'bar']))
    vec = ri.ListSexpVector(seq)
    vec_s = vec[0:2]
    assert len(vec_s) == 2
    utils.assert_equal_sequence(vec_s[0], ri.FloatSexpVector([1.0]))
    utils.assert_equal_sequence(vec_s[1], ri.IntSexpVector([2, 3]))


def test_setslice():
    seq = (ri.FloatSexpVector([1.0]),
           ri.IntSexpVector([2, 3]),
           ri.StrSexpVector(['foo', 'bar']))
    vec = ri.ListSexpVector(seq)
    vec[0:2] = ri.ListSexpVector(
        [ri.FloatSexpVector([10.0]),
         ri.IntSexpVector([20, 30])]
    )
    assert len(vec) == 3
    utils.assert_equal_sequence(vec[0], ri.FloatSexpVector([10.0]))
    utils.assert_equal_sequence(vec[1], ri.IntSexpVector([20, 30]))
    utils.assert_equal_sequence(vec[2], ri.StrSexpVector(['foo', 'bar']))
