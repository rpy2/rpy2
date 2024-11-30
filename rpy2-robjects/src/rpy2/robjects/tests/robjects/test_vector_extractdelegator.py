import array
import pytest
import rpy2.rinterface_lib.callbacks
import rpy2.rinterface_lib.embedded
import rpy2.rlike.container as rlc
from rpy2 import robjects
from rpy2.rinterface.tests import utils


def _just_pass(s):
    pass


@pytest.fixture(scope='module')
def silent_console_print():
    with utils.obj_in_module(rpy2.rinterface_lib.callbacks, 'consolewrite_print', _just_pass):
        yield


def test_extract_getitem_by_index():
    seq_R = robjects.baseenv["seq"]
    mySeq = seq_R(0, 10)
    # R indexing starts at one
    myIndex = robjects.vectors.IntVector(array.array('i', range(1, 11, 2)))

    mySubset = mySeq.rx[myIndex]
    for i, si in enumerate(myIndex):
        assert mySeq[si-1] == mySubset[i]


def test_extract_by_index():
    seq_R = robjects.baseenv["seq"]
    mySeq = seq_R(0, 10)
    # R indexing starts at one
    myIndex = robjects.vectors.IntVector(array.array('i', range(1, 11, 2)))

    mySubset = mySeq.rx(myIndex, drop=True)
    for i, si in enumerate(myIndex):
        assert mySeq[si-1] == mySubset[i]


def test_extract_by_name():
    seq_R = robjects.baseenv["seq"]
    mySeq = seq_R(0, 25)

    letters = robjects.baseenv["letters"]
    mySeq = robjects.baseenv["names<-"](mySeq, 
                                        letters)

    # R indexing starts at one
    myIndex = robjects.vectors.StrVector(letters[2])

    mySubset = mySeq.rx(myIndex)

    for i, si in enumerate(myIndex):
        assert mySubset[i] == 2


def test_extract_silent_index_error():
    seq_R = robjects.baseenv["seq"]
    mySeq = seq_R(0, 10)
    # R indexing starts at one.
    myIndex = robjects.vectors.StrVector(['a', 'b', 'c'])

    with utils.obj_in_module(rpy2.rinterface_lib.callbacks,
                             'consolewrite_print',
                             utils.noconsole):
        res = mySeq.rx(myIndex)
        assert all(x == rpy2.robjects.NA_Integer for x in res)


def test_replace():
    vec = robjects.vectors.IntVector(range(1, 6))
    i = array.array('i', [1, 3])
    vec.rx[rlc.TaggedList((i, ))] = 20
    assert vec[0] == 20
    assert vec[1] == 2
    assert vec[2] == 20
    assert vec[3] == 4

    vec = robjects.vectors.IntVector(range(1, 6))
    i = array.array('i', [1, 5])
    vec.rx[rlc.TaggedList((i, ))] = 50
    assert vec[0] == 50
    assert vec[1] == 2
    assert vec[2] == 3
    assert vec[3] == 4
    assert vec[4] == 50

    vec = robjects.vectors.IntVector(range(1, 6))
    vec.rx[1] = 70
    assert tuple(vec[0:5]) == (70, 2, 3, 4, 5)

    vec = robjects.vectors.IntVector(range(1, 6))
    vec.rx[robjects.vectors.IntVector((1, 3))] = 70    
    assert tuple(vec[0:5]) == (70, 2, 70, 4, 5)

    m = robjects.r('matrix(1:10, ncol=2)')
    m.rx[1, 1] = 9
    assert m[0] == 9

    m = robjects.r('matrix(1:10, ncol=2)')
    m.rx[2, robjects.vectors.IntVector((1,2))] = 9
    assert m[1] == 9
    assert m[6] == 9


def test_extract_recycling_rule():
    # Create a vector with 22 cells.
    v = robjects.vectors.IntVector(array.array('i', range(1, 23)))
    # Promote it to a matrix with 2 columns (therefore 11 rows).
    m = robjects.r.matrix(v, ncol = 2)
    # Extraxt all elements in the first column (R is one-indexed).
    col = m.rx(True, 1)
    assert len(col) == 11


def test_extract_list():
    # list
    letters = robjects.baseenv['letters']
    myList = robjects.baseenv['list'](l=letters, f='foo')
    idem = robjects.baseenv['identical']
    assert idem(letters, myList.rx('l')[0])[0]
    assert idem('foo', myList.rx('f')[0])[0]
