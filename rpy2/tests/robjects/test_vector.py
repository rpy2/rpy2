import pytest
import rpy2.robjects as robjects
ri = robjects.rinterface
import os
import array
import time
import datetime
import rpy2.rlike.container as rlc
from collections import OrderedDict

rlist = robjects.baseenv["list"]


def test_init():
    identical = ri.baseenv["identical"]
    py_a = array.array('i', [1,2,3])
    ro_v = robjects.IntVector(py_a)
    assert ro_v.typeof == ri.RTYPES.INTSXP

    ri_v = ri.IntSexpVector(py_a)
    ro_v = robjects.IntVector(ri_v)

    assert identical(ro_v, ri_v)[0]

    del(ri_v)
    assert ro_v.typeof == ri.RTYPES.INTSXP


@pytest.mark.parametrize(
    'cls,expected_na',
    [(robjects.StrVector, ri.NA_Character),
     (robjects.IntVector, ri.NA_Integer),
     (robjects.FloatVector, ri.NA_Real),
     (robjects.BoolVector, ri.NA_Logical),
     (robjects.ComplexVector, ri.NA_Complex),
    ])
def test_vector_navalue(cls, expected_na):
    assert cls.NAvalue is expected_na


@pytest.mark.parametrize(
    'cls,values',
    [(robjects.StrVector, ['abc', 'def']),
     (robjects.IntVector, [123, 456]),
     (robjects.FloatVector, [123.0, 456.0]),
     (robjects.BoolVector, [True, False])])
def test_init_vectors(cls, values):
    vec = cls(values)
    assert len(vec) == len(values)
    for x, y in zip(vec, values):
        assert x == y


@pytest.mark.parametrize(
    'vec',
    (robjects.ListVector({'a': 1, 'b': 2}),
     robjects.ListVector((('a', 1), ('b', 2))),
     robjects.ListVector(iter([('a', 1), ('b', 2)])))
)
def test_new_listvector(vec):
    assert 'a' in vec.names
    assert 'b' in vec.names
    assert len(vec) == 2
    assert len(vec.names) == 2


def test_strvector_factor():
    vec = robjects.StrVector(('abc', 'def', 'abc'))
    fvec = vec.factor()
    assert isinstance(fvec, robjects.FactorVector)


def test_add_operator():
    seq_R = robjects.r["seq"]
    mySeqA = seq_R(0, 3)
    mySeqB = seq_R(5, 7)
    mySeqAdd = mySeqA + mySeqB

    assert len(mySeqA)+len(mySeqB) == len(mySeqAdd)

    for i, li in enumerate(mySeqA):
        assert mySeqAdd[i] == li
    for j, li in enumerate(mySeqB):
        assert mySeqAdd[i+j+1] == li


def test_r_add_operator():
    seq_R = robjects.r["seq"]
    mySeq = seq_R(0, 10)
    mySeqAdd = mySeq.ro + 2
    for i, li in enumerate(mySeq):
        assert li + 2 == mySeqAdd[i]


def test_r_sub_operator():
    seq_R = robjects.r["seq"]
    mySeq = seq_R(0, 10)
    mySeqAdd = mySeq.ro - 2
    for i, li in enumerate(mySeq):
        assert li - 2 == mySeqAdd[i]


def test_r_mult_operator():
    seq_R = robjects.r["seq"]
    mySeq = seq_R(0, 10)
    mySeqAdd = mySeq.ro * 2
    for i, li in enumerate(mySeq):
        assert li * 2 == mySeqAdd[i]


def test_r_matmul_operator():
    # 1 3
    # 2 4
    m = robjects.r.matrix(robjects.IntVector(range(1, 5)), nrow=2)
    # 1*1+3*2 1*3+3*4
    # 2*1+4*2 2*3+4*4
    m2 = m.ro @ m
    for i,val in enumerate((7.0, 10.0, 15.0, 22.0,)):
        assert m2[i] == val


def test_r_power_operator():
    seq_R = robjects.r["seq"]
    mySeq = seq_R(0, 10)
    mySeqPow = mySeq.ro ** 2
    for i, li in enumerate(mySeq):
        assert li ** 2 == mySeqPow[i]

def test_r_truediv():
    v = robjects.vectors.IntVector((2,3,4))
    res = v.ro / 2
    assert all(abs(x-y) < 0.001 for x, y in zip(res, (1, 1.5, 2)))


def test_r_floor_division():
    v = robjects.vectors.IntVector((2, 3, 4))
    res = v.ro // 2
    assert tuple(int(x) for x in res) == (1, 1, 2)


def test_r_mod():
    v = robjects.vectors.IntVector((2, 3, 4))
    res = v.ro % 2
    assert all(x == y for x, y in zip(res,
                                      (0, 1, 0)))


def test_r_and():
    v = robjects.vectors.BoolVector((True, False))
    res = v.ro & True
    assert all(x is y for x, y in zip(res, (True, False)))


def test_r_or():
    v = robjects.vectors.BoolVector((True, False))
    res = v.ro | False
    assert all(x is y for x, y in zip(res, (True, False)))


def test_r_invert():
    v = robjects.vectors.BoolVector((True, False))
    res = ~v.ro
    assert all(x is (not y) for x, y in zip(res, (True, False)))


def test_r_lt():
    v = robjects.vectors.IntVector((4, 2, 1))
    res = v.ro < 2
    assert all(x is y for x, y in zip(res, (False, False, True)))


def test_r_le():
    v = robjects.vectors.IntVector((4, 2, 1))
    res = (v.ro <= 2)
    assert all(x is y for x, y in zip(res, (False, True, True)))


def test_r_gt():
    v = robjects.vectors.IntVector((4, 2, 1))
    res = v.ro > 2
    assert all(x is y for x, y in zip(res, (True, False, False)))


def test_r_ge():
    v = robjects.vectors.IntVector((4, 2, 1))
    res = v.ro >= 2
    assert all(x is y for x, y in zip(res, (True, True, False)))


def test_r_eq():
    v = robjects.vectors.IntVector((4, 2, 1))
    res = v.ro == 2
    assert all(x is y for x, y in zip(res, (False, True, False)))


def test_r_ne():
    v = robjects.vectors.IntVector((4, 2, 1))
    res = v.ro != 2
    assert all(x is y for x, y in zip(res, (True, False, True)))


def test_r_neg():
    v = robjects.vectors.IntVector((4, 2, 1))
    res = - v.ro
    assert all(x is y for x, y in zip(res, (-4, -2, -1)))


def test_contains():
    v = robjects.StrVector(('abc', 'def', 'ghi'))
    assert 'def' in v.ro
    assert 'foo' not in v.ro


@pytest.mark.parametrize(
    'cls,values',
    [(robjects.StrVector, ['abc', 'def']),
     (robjects.IntVector, [123, 456]),
     (robjects.FloatVector, [123.0, 456.0]),
     (robjects.BoolVector, [True, False])])
def test_getitem_int(cls, values):
    vec = cls(values)
    assert vec[0] == values[0]
    assert vec[1] == values[1]


def test_getitem_outofbounds():
    letters = robjects.baseenv["letters"]
    with pytest.raises(IndexError):
        letters[26]

@pytest.mark.parametrize(
    'cls,values',
    [(robjects.StrVector, ['abc', 'def']),
     (robjects.IntVector, [123, 456]),
     (robjects.FloatVector, [123.0, 456.0]),
     (robjects.BoolVector, [True, False])])
def test_getitem_invalidtype(cls, values):
    vec = cls(values)
    with pytest.raises(TypeError):
        vec['foo']


def test_setitem():
    vec = robjects.r.seq(1, 10)
    assert vec[0] == 1
    vec[0] = 20
    assert vec[0] == 20


def test_setitem_outofbounds():
    vec = robjects.r.seq(1, 10)
    with pytest.raises(IndexError):
        vec[20] = 20


@pytest.mark.parametrize(
    'cls,values',
    [(robjects.StrVector, ['abc', 'def']),
     (robjects.IntVector, [123, 456]),
     (robjects.FloatVector, [123.0, 456.0]),
     (robjects.BoolVector, [True, False])])
def test_setitem_invalidtype(cls, values):
    vec = cls(values)
    with pytest.raises(TypeError):
        vec['foo'] = values[0]


def get_item_list():
    mylist = rlist(letters, "foo")
    idem = robjects.baseenv["identical"]
    assert idem(letters, mylist[0])[0] is True
    assert idem("foo", mylist[1])[0] is True


def test_getnames():
    vec = robjects.vectors.IntVector(array.array('i', [1,2,3]))
    v_names = [robjects.baseenv["letters"][x] for x in (0,1,2)]
    #FIXME: simplify this
    r_names = robjects.baseenv["c"](*v_names)
    vec = robjects.baseenv["names<-"](vec, r_names)
    for i in range(len(vec)):
        assert v_names[i] == vec.names[i]
    vec.names[0] = 'x'


def test_setnames():
    vec = robjects.vectors.IntVector(array.array('i', [1,2,3]))
    names = ['x', 'y', 'z']
    vec.names = names
    for i in range(len(vec)):
        assert names[i] == vec.names[i]


def test_nainteger():
    vec = robjects.IntVector(range(3))
    vec[0] = robjects.NA_Integer
    assert robjects.baseenv['is.na'](vec)[0] is True


def test_tabulate():
    vec = robjects.IntVector((1,2,1,2,1,2,2))
    tb = vec.tabulate()
    assert tuple(tb) == (3, 4)


def test_nareal():
    vec = robjects.FloatVector((1.0, 2.0, 3.0))
    vec[0] = robjects.NA_Real
    assert robjects.baseenv['is.na'](vec)[0] is True


def test_nalogical():
    vec = robjects.BoolVector((True, False, True))
    vec[0] = robjects.NA_Logical
    assert robjects.baseenv['is.na'](vec)[0] is True


@pytest.mark.xfail(reason='Edge case with conversion.')
def test_nacomplex():
    vec = robjects.ComplexVector((1+1j, 2+2j, 3+3j))
    vec[0] = robjects.NA_Complex
    assert robjects.baseenv['is.na'](vec)[0] is True

def test_nacomplex_workaround():
    vec = robjects.ComplexVector((1+1j, 2+2j, 3+3j))
    vec[0] = complex(robjects.NA_Complex.real, robjects.NA_Complex.imag)
    assert robjects.baseenv['is.na'](vec)[0] is True

def test_nacharacter():
    vec = robjects.StrVector('abc')
    vec[0] = robjects.NA_Character
    assert robjects.baseenv['is.na'](vec)[0] is True


def test_int_repr():
    vec = robjects.vectors.IntVector((1, 2, ri.NA_Integer))
    s = repr(vec)
    assert s.endswith('[1, 2, NA_integer_]')


def test_list_repr():
    vec = robjects.vectors.ListVector((('a', 1),
                                       ('b', 2),
                                       ('b', 3)))
    s = repr(vec)
    assert s.startswith('<rpy2.robjects.vectors.ListVector ')

    vec2 = robjects.vectors.ListVector((('A', vec),))
    s = repr(vec2)
    assert s.startswith('<rpy2.robjects.vectors.ListVector ')


def test_float_repr():
    vec = robjects.vectors.FloatVector((1,2,3))
    r = repr(vec).split('\n')
    assert r[-1].startswith('[')
    assert r[-1].endswith(']')
    assert len(r[-1].split(',')) == 3


@pytest.mark.parametrize(
    'params',
    ((robjects.vectors.DataFrame,
      dict((('a', ri.IntSexpVector((1, 2, 3))),
            ('b', ri.IntSexpVector((4, 5, 6))),
            ('c', ri.IntSexpVector((7, 8, 9))),
            ('d', ri.IntSexpVector((7, 8, 9))),
            ('e', ri.IntSexpVector((7, 8, 9))),
      ))),
     (robjects.vectors.IntVector,
      (1, 2, 3, 4, 5)),
     (robjects.vectors.ListVector,
      (('a', 1), ('b', 2), ('b', 3), ('c', 4), ('d', 5))),
     (robjects.vectors.FloatVector,
      (1, 2, 3, 4, 5)))
)
def test_repr_html(params):
    vec_cls, data = params
    vec = vec_cls(data)
    s = vec._repr_html_().split('\n')
    assert s[2].strip().startswith('<table>')
    assert s[-2].strip().endswith('</table>')

    s = vec._repr_html_(max_items=2).split('\n')
    assert s[2].strip().startswith('<table>')
    assert s[-2].strip().endswith('</table>')


def test_repr_nonvectorinlist():
    vec = robjects.ListVector(OrderedDict((('a', 1), 
                                           ('b', robjects.Formula('y ~ x')),
                                           )))
    s = repr(vec).split(os.linesep)
    assert s[1].startswith("R classes: ('list',)")
    assert s[2].startswith("[IntSexpVector, LangSexpVector]")


def test_items():
    vec = robjects.IntVector(range(3))
    vec.names = robjects.StrVector('abc')
    names = [k for k,v in vec.items()]
    assert names == ['a', 'b', 'c']
    values = [v for k,v in vec.items()]
    assert values == [0, 1, 2]


def test_itemsnonames():
    vec = robjects.IntVector(range(3))
    names = [k for k,v in vec.items()]
    assert names == [None, None, None]
    values = [v for k,v in vec.items()]
    assert values == [0, 1, 2]


def test_sequence_to_vector():
    res = robjects.sequence_to_vector((1, 2, 3))
    assert isinstance(res, robjects.IntVector)

    res = robjects.sequence_to_vector((1, 2, 3.0))
    assert isinstance(res, robjects.FloatVector)

    res = robjects.sequence_to_vector(('ab', 'cd', 'ef'))
    assert isinstance(res, robjects.StrVector)

    with pytest.raises(ValueError):
        robjects.sequence_to_vector(list())


def test_sample():
    vec = robjects.IntVector(range(100))
    spl = vec.sample(10)
    assert len(spl) == 10


def test_sample_probabilities():
    vec = robjects.IntVector(range(100))
    spl = vec.sample(10, probabilities=robjects.FloatVector([.01] * 100))
    assert len(spl) == 10


def test_sample_probabilities_novector():
    vec = robjects.IntVector(range(100))
    spl = vec.sample(10, probabilities=[.01] * 100)
    assert len(spl) == 10


def test_sample_probabilities_error_len():
    vec = robjects.IntVector(range(100))
    with pytest.raises(ValueError):
        vec.sample(10,
                   probabilities=robjects.FloatVector([.01] * 10))


def test_sample_error():
    vec = robjects.IntVector(range(100))
    with pytest.raises(ri.embedded.RRuntimeError):
        spl = vec.sample(110)


def test_sample_replacement():
    vec = robjects.IntVector(range(100))
    spl = vec.sample(110, replace=True)
    assert len(spl) == 110
