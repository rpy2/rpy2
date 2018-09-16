import pytest
import rpy2.rinterface as rinterface
from rpy2.rinterface import bufferprotocol

rinterface.initr()


def test_getrank():
    v = rinterface.IntSexpVector([1,2,3])
    assert bufferprotocol.getrank(v.__sexp__._cdata) == 1

    m = rinterface.baseenv.get('matrix')(nrow=2, ncol=2)
    assert bufferprotocol.getrank(m.__sexp__._cdata) == 2


def test_getshape():
    v = rinterface.IntSexpVector([1,2,3])
    assert bufferprotocol.getshape(v.__sexp__._cdata, 1) == [3]

    m = rinterface.baseenv.get('matrix')(nrow=2, ncol=3)
    assert bufferprotocol.getshape(m.__sexp__._cdata, 2) == [2, 3]
