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


@pytest.mark.parametrize(
    'r_string,idx,value,expected',
    (
        ('1:5', rlc.NamedList((array.array('i', [1, 3]), )),
         20, (20, 2, 20, 4, 5)),
        ('1:5', rlc.NamedList((array.array('i', [1, 5]), )),
         50, (50, 2, 3, 4, 50)),
        ('1:5', 1, 70, (70, 2, 3, 4, 5)),
        ('1:5', robjects.vectors.IntVector((1, 3)),
         70, (70, 2, 70, 4, 5))
    )
)
def test_replace_vec(r_string, idx, value, expected):
    vec = robjects.r(r_string)
    vec.rx[idx] = value
    assert tuple(vec) == expected


@pytest.mark.parametrize(
    'r_string,idx,value,expected',
    (
        ('matrix(1:10, ncol=2)', (1, 1), 9,
         (9, 2, 3, 4, 5, 6, 7, 8, 9, 10)),
        ('matrix(1:10, ncol=2)',
         (2, robjects.vectors.IntVector((1,2))), 9,
         (1, 9, 3, 4, 5, 6, 9, 8, 9, 10))
    )
)
def test_replace_matrix(r_string, idx, value, expected):

    vec = robjects.r(r_string)
    vec.rx.__setitem__(idx, value)
    assert tuple(vec) == expected


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
