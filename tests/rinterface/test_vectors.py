import multiprocessing
import pytest
import struct
import sys
import unittest
import rpy2.rinterface as ri

ri.initr()


# TODO: make this an rinterface function
def evalr(string):
    res = ri.parse(string)
    res = ri.baseenv["eval"](res)
    return res


def floatEqual(x, y, epsilon = 0.00000001):
    return abs(x - y) < epsilon


def test_int():
    sexp = ri.IntSexpVector([1, ])
    isInteger = ri.globalenv.get("is.integer")
    assert isInteger(sexp)[0]

    
def test_float():
    sexp = ri.IntSexpVector([1.0, ])
    isNumeric = ri.globalenv.get("is.numeric")
    assert isNumeric(sexp)[0]


def test_str():
    sexp = ri.StrSexpVector(["a", ])
    isStr = ri.globalenv.get("is.character")
    assert isStr(sexp)[0]


def test_bool():
    sexp = ri.BoolSexpVector([True, ])
    isBool = ri.globalenv.get("is.logical")
    assert isBool(sexp)[0]


def test_complex():
    sexp = ri.ComplexSexpVector([1+2j, ])
    is_complex = ri.globalenv.get("is.complex")
    assert is_complex(sexp)[0]


def test_byte():
    seq = (b'a', b'b')
    sexp = ri.ByteSexpVector(seq)
    is_raw = ri.globalenv.get("is.raw")
    assert is_raw(sexp)[0]


def test_del():
    v = ri.IntSexpVector(range(10))
    with pytest.raises(AttributeError):
        v.__delitem__(3)


def test_from_bool():
    sexp = ri.vector([True, ], ri.RTYPES.LGLSXP)
    isLogical = ri.globalenv.get('is.logical')
    assert isLogical(sexp)[0]
    assert sexp[0] == True

    sexp = ri.vector(['a', ], ri.RTYPES.LGLSXP)
    isLogical = ri.globalenv.get('is.logical')
    assert isLogical(sexp)[0]
    assert sexp[0]


def test_from_int():
    sexp = ri.vector([1, ], ri.RTYPES.INTSXP)
    isInteger = ri.globalenv.get('is.integer')
    assert isInteger(sexp)[0]
    
    with pytest.raises(ValueError):
        ri.vector(['a', ], ri.RTYPES.INTSXP)


def test_from_invalid_no_length():
    s = (x for x in range(30))
    with pytest.raises(TypeError):
        ri.vector(s, ri.RTYPES.INTSXP)


def test_from_float():
    sexp = ri.vector([1.0, ], ri.RTYPES.REALSXP)
    isNumeric = ri.globalenv.get("is.numeric")
    assert isNumeric(sexp)[0]

    
def test_from_float_nan():
    with pytest.raises(ValueError):
        ri.vector(["a", ], ri.RTYPES.REALSXP)


def test_from_complex():
    sexp = ri.vector([1.0 + 1.0j, ], ri.RTYPES.CPLXSXP)
    isComplex = ri.globalenv.get('is.complex')
    assert isComplex(sexp)[0]


def test_from_string():
    sexp = ri.vector(['abc', ], ri.RTYPES.STRSXP)
    isCharacter = ri.globalenv.get('is.character')
    assert isCharacter(sexp)[0]


def test_from_list():
    seq = (ri.FloatSexpVector([1.0]),
           ri.IntSexpVector([2, 3]),
           ri.StrSexpVector(['foo', 'bar']))
    sexp = ri.ListSexpVector(seq)
    isList = ri.globalenv.get('is.list')
    assert isList(sexp)[0]
    assert len(sexp) == 3

    
def test_missing_R_Preserve_object_bug():
    rgc = ri.baseenv['gc']
    xx = range(100000)
    x = ri.IntSexpVector(xx)
    rgc()    
    assert x[0] == 0


def test_invalid_rtype():
    with pytest.raises(ValueError):
        ri.vector([1, ], -1)
    with pytest.raises(ValueError):
        ri.vector([1, ], 250)
    

def test_invalid_not_vector_rtype():
    with pytest.raises(ValueError):
        ri.vector([1, ], ri.RTYPES.ENVSXP)


@pytest.mark.skip(reason='Spawned process seems to share initialization state with parent.')
def test_instantiate_without_initr():
    def foo(queue):
        import rpy2.rinterface as rinterface
        try:
            tmp = ri.vector([1,2], ri.INTSXP)
            res = (False, None)
        except RuntimeError as re:
            res = (True, re)
        except Exception as e:
            res = (False, e)
        queue.put(res)
    q = multiprocessing.Queue()
    ctx = multiprocessing.get_context('spawn')
    p = ctx.Process(target = foo, args = (q,))
    p.start()
    res = q.get()
    p.join()
    assert res[0] is True
