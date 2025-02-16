import rpy2.rinterface as rinterface
from rpy2.rinterface import bufferprotocol

rinterface.initr()


def test_getrank():
    v = rinterface.IntSexpVector([1, 2, 3])
    assert bufferprotocol.getrank(v.__sexp__._cdata) == 1

    m = rinterface.baseenv.find('matrix')(nrow=2, ncol=2)
    assert bufferprotocol.getrank(m.__sexp__._cdata) == 2


def test_getshape():
    v = rinterface.IntSexpVector([1, 2, 3])
    assert bufferprotocol.getshape(v.__sexp__._cdata, 1) == (3, )

    m = rinterface.baseenv.find('matrix')(nrow=2, ncol=3)
    assert bufferprotocol.getshape(m.__sexp__._cdata, 2) == (2, 3)


def test_getstrides():
    v = rinterface.IntSexpVector([1, 2, 3])
    assert bufferprotocol.getstrides(v.__sexp__._cdata, [3], 8) == (8, )

    m = rinterface.baseenv.find('matrix')(nrow=2, ncol=3)
    shape = (2, 3)
    sizeof = 8
    # 1, 3, 5
    # 2, 4, 6
    expected = (sizeof, shape[0] * sizeof)
    assert (bufferprotocol
            .getstrides(m.__sexp__._cdata, shape, sizeof)) == expected
