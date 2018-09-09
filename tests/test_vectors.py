import multiprocessing
import pytest
import sys, struct
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


def test_missing_type():
    with pytest.raises(ValueError):
        ri.vector([2, ])


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
    
    sexp = ri.SexpVector(['a', ], ri.RTYPES.INTSXP)
    isNA = ri.globalenv.get('is.na')
    assert isNA(sexp)[0]


def test_from_int_invalid():
    s = set((0,1))
    with pytest.raises(ValueError):
        ri.vector(s, ri.RTYPES.INTSXP)


def test_from_float():
    sexp = ri.SexpVector([1.0, ], ri.RTYPES.REALSXP)
    isNumeric = ri.globalenv.get("is.numeric")
    assert isNumeric(sexp)[0]

    sexp = ri.SexpVector(["a", ], ri.RTYPES.REALSXP)
    isNA = ri.globalenv.get("is.na")
    assert isNA(sexp)[0]


def test_from_complex():
    sexp = ri.vector([1.0 + 1.0j, ], ri.RTYPES.CPLXSXP)
    isComplex = ri.globalenv.get('is.complex')
    assert isComplex(sexp)[0]


def test_from_string():
    sexp = ri.vector(['abc', ], ri.RTYPES.STRSXP)
    isCharacter = ri.globalenv.get('is.character')
    assert isCharacter(sexp)[0]

    sexp = ri.vector([1, ], ri.RTYPES.STRSXP)
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


def test_setitem_different_type():
    vec = ri.IntSexpVector([0, 1, 2, 3, 4, 5])
    with pytest.raises(ValueError):
        vec.__setitem__(0,
                        ri.StrSexpVector(['abc', ]))


def test_invalid_rtype():
    with pytest.raises(ValueError):
        ri.vector([1, ], -1)
    with pytest.raises(ValueError):
        ri.vector([1, ], 250)
    

def test_invalid_not_vector_rtype():
    with pytest.raises(ValueError):
        ri.vector([1, ], ri.RTYPES.ENVSXP)


class SexpVectorTestCase(unittest.TestCase):

    @pytest.mark.skip(reason='Spawned process seems to share initialization state with parent.')
    def testNewWithoutInit():
        def foo(queue):
            import rpy2.rinterface as rinterface
            try:
                tmp = ri.SexpVector([1,2], ri.INTSXP)
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
        self.assertTrue(res[0])
        
    def testGetItemPairList():
        pairlist = ri.baseenv.get('pairlist')
        pl = pairlist(a = ri.StrSexpVector(['1', ]))
        # R's behaviour is that subsetting returns an R list
        y = pl[0]
        self.assertEqual(ri.VECSXP, y.typeof)
        self.assertEqual('a', y.do_slot('names')[0])
        self.assertEqual('1', y[0][0])

    def testGetSlicePairllist():
        # Checks that root of issue #380 is fixed
        vec = ri.baseenv['.Options']
        vec_slice = vec[0:2]
        self.assertEqual(2, len(vec_slice))
        self.assertEqual(ri.LISTSXP, vec_slice.typeof)
        self.assertEqual(vec.do_slot("names")[0], vec_slice.do_slot("names")[0])
        self.assertEqual(vec.do_slot("names")[1], vec_slice.do_slot("names")[1])

