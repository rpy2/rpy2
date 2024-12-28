import pytest
import rpy2.rinterface as ri

ri.initr()


def test_init_from_seqr():
    seq = ['foo', 'bar', 'baz']
    v = ri.StrSexpVector(seq)
    assert len(v) == 3
    for x, y in zip(seq, v):
        assert x == y


def test_init_from_seq_invalid_item():
    seq = ['foo', 0, 'baz']
    with pytest.raises(Exception):
        ri.StrSexpVector(seq)


def test_getitem():
    vec = ri.StrSexpVector(['foo', 'bar', 'baz'])
    assert vec[1] == 'bar'
    with pytest.raises(TypeError):
        vec[(2, 3)]


@pytest.mark.parametrize('value',
                         ('boo', ri.NA_Character))
def test_setitem(value):
    vec = ri.StrSexpVector(['foo', 'bar', 'baz'])
    vec[1] = value
    assert vec[1] == value
    with pytest.raises(TypeError):
        vec[(2, 3)] = value


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
    vec[0:2] = ['boo', 'noo']
    assert len(vec) == 3
    assert vec[0] == 'boo'
    assert vec[1] == 'noo'


def test_setslice_negative():
    vec = ri.StrSexpVector(['foo', 'bar', 'baz'])
    vec[-2:-1] = ri.StrSexpVector(['boo', ])
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


def test_non_asciil():
    u_char = '\u21a7'
    b_char = b'\xe2\x86\xa7'
    assert(b_char == u_char.encode('utf-8'))
    sexp = ri.StrSexpVector((u'\u21a7', ))
    char = sexp[0]
    assert isinstance(char, str)
    # FIXME: the following line is failing on drone, but not locally
    assert u'\u21a7'.encode('utf-8') == char.encode('utf-8')
    # because of this, the following line is used to pass the test
    # until I have more reports from users or manage to reproduce
    # myself what is happening on drone.io.
    sexp = ri.evalr('c("ěščřžýáíé", "abc", "百折不撓")')
    assert all(isinstance(x, str) for x in sexp)
    
