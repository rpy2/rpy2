import multiprocessing
import pytest
import struct
import sys
import unittest
import rpy2.rinterface as ri

ri.initr()


def floatEqual(x, y, epsilon = 0.00000001):
    return abs(x - y) < epsilon


def test_int():
    sexp = ri.IntSexpVector([1, ])
    isInteger = ri.globalenv.find("is.integer")
    assert isInteger(sexp)[0]

    
def test_float():
    sexp = ri.IntSexpVector([1.0, ])
    isNumeric = ri.globalenv.find("is.numeric")
    assert isNumeric(sexp)[0]


def test_str():
    sexp = ri.StrSexpVector(["a", ])
    isStr = ri.globalenv.find("is.character")
    assert isStr(sexp)[0]


def test_bool():
    sexp = ri.BoolSexpVector([True, ])
    isBool = ri.globalenv.find("is.logical")
    assert isBool(sexp)[0]


def test_complex():
    sexp = ri.ComplexSexpVector([1+2j, ])
    is_complex = ri.globalenv.find("is.complex")
    assert is_complex(sexp)[0]


def test_byte():
    seq = (b'a', b'b')
    sexp = ri.ByteSexpVector(seq)
    is_raw = ri.globalenv.find("is.raw")
    assert is_raw(sexp)[0]


def test_del():
    v = ri.IntSexpVector(range(10))
    with pytest.raises(AttributeError):
        v.__delitem__(3)


def test_from_bool():
    sexp = ri.vector([True, ], ri.RTYPES.LGLSXP)
    isLogical = ri.globalenv.find('is.logical')
    assert isLogical(sexp)[0]
    assert sexp[0] == True

    sexp = ri.vector(['a', ], ri.RTYPES.LGLSXP)
    isLogical = ri.globalenv.find('is.logical')
    assert isLogical(sexp)[0]
    assert sexp[0]


def test_from_int():
    sexp = ri.vector([1, ], ri.RTYPES.INTSXP)
    isInteger = ri.globalenv.find('is.integer')
    assert isInteger(sexp)[0]
    
    with pytest.raises(ValueError):
        ri.vector(['a', ], ri.RTYPES.INTSXP)


def test_from_invalid_no_length():
    s = (x for x in range(30))
    with pytest.raises(TypeError):
        ri.vector(s, ri.RTYPES.INTSXP)


def test_from_float():
    sexp = ri.vector([1.0, ], ri.RTYPES.REALSXP)
    isNumeric = ri.globalenv.find("is.numeric")
    assert isNumeric(sexp)[0]

    
def test_from_float_nan():
    with pytest.raises(ValueError):
        ri.vector(["a", ], ri.RTYPES.REALSXP)


def test_from_complex():
    sexp = ri.vector([1.0 + 1.0j, ], ri.RTYPES.CPLXSXP)
    isComplex = ri.globalenv.find('is.complex')
    assert isComplex(sexp)[0]


def test_from_string():
    sexp = ri.vector(['abc', ], ri.RTYPES.STRSXP)
    isCharacter = ri.globalenv.find('is.character')
    assert isCharacter(sexp)[0]


def test_from_list():
    seq = (ri.FloatSexpVector([1.0]),
           ri.IntSexpVector([2, 3]),
           ri.StrSexpVector(['foo', 'bar']))
    sexp = ri.ListSexpVector(seq)
    isList = ri.globalenv.find('is.list')
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


def _run_without_initr(queue):
    import rpy2.rinterface as rinterface
    try:
        tmp = rinterface.vector([1,2], rinterface.RTYPES.INTSXP)
        res = (True, None)
    except rinterface.embedded.RNotReadyError as re:
        res = (False, None)
    except Exception as e:
        res = (False, str(e))
    queue.put(res)

        
def test_instantiate_without_initr():
    ctx = multiprocessing.get_context('spawn')
    q = ctx.Queue()
    p = ctx.Process(target = _run_without_initr, args = (q,))
    p.start()
    res = q.get()
    p.join()
    assert res == (False, None)
