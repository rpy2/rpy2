import array
import pytest
from rpy2 import robjects
from .. import utils


def _just_pass(s):
    pass


@pytest.fixture(scope='module')
def silent_console_print():
    with utils.obj_in_module(rinterface.callbacks, 'consolewrite_print', _just_pass):
        yield


def test_floor_division():
    v = robjects.vectors.IntVector((2,3,4))
    res = v.ro // 2
    assert tuple(int(x) for x in res) == (1,1,2)


@pytest.mark.skip(reason='segfault')
def test_extract_by_index():
    seq_R = robjects.baseenv["seq"]
    mySeq = seq_R(0, 10)
    # R indexing starts at one
    myIndex = robjects.Vector(array.array('i', range(1, 11, 2)))

    mySubset = mySeq.rx(myIndex)
    for i, si in enumerate(myIndex):
        assert mySeq[si-1] == mySubset[i]


def test_extract_by_name():
    seq_R = robjects.baseenv["seq"]
    mySeq = seq_R(0, 25)

    letters = robjects.baseenv["letters"]
    mySeq = robjects.baseenv["names<-"](mySeq, 
                                                 letters)

    # R indexing starts at one
    myIndex = robjects.Vector(letters[2])

    mySubset = mySeq.rx(myIndex)

    for i, si in enumerate(myIndex):
        assert mySubset[i] == 2


def test_extract_index_error():
    seq_R = robjects.baseenv["seq"]
    mySeq = seq_R(0, 10)
    # R indexing starts at one
    myIndex = robjects.Vector(['a', 'b', 'c'])

    def noconsole(x):
        pass
    robjects.rinterface.set_writeconsole_regular(noconsole)

    with pytest.raises(ri.RRuntimeError):
        mySeq.rx(myIndex)


def test_replace():
    vec = robjects.IntVector(range(1, 6))
    i = array.array('i', [1, 3])
    vec.rx[rlc.TaggedList((i, ))] = 20
    assert vec[0] == 20
    assert vec[1] == 2
    assert vec[2] == 20
    assert vec[3] == 4

    vec = robjects.IntVector(range(1, 6))
    i = array.array('i', [1, 5])
    vec.rx[rlc.TaggedList((i, ))] = 50
    assert vec[0] == 50
    assert vec[1] == 2
    assert vec[2] == 3
    assert vec[3] == 4
    assert vec[4] == 50

    vec = robjects.IntVector(range(1, 6))
    vec.rx[1] = 70
    self.assertEqual(70, vec[0])
    self.assertEqual(2, vec[1])
    self.assertEqual(3, vec[2])
    self.assertEqual(4, vec[3])
    self.assertEqual(5, vec[4])

    vec = robjects.IntVector(range(1, 6))
    vec.rx[robjects.IntVector((1, 3))] = 70
    self.assertEqual(70, vec[0])
    self.assertEqual(2, vec[1])
    self.assertEqual(70, vec[2])
    self.assertEqual(4, vec[3])
    self.assertEqual(5, vec[4])


    m = robjects.r('matrix(1:10, ncol=2)')
    m.rx[1, 1] = 9
    self.assertEqual(9, m[0])

    m = robjects.r('matrix(1:10, ncol=2)')
    m.rx[2, robjects.IntVector((1,2))] = 9
    self.assertEqual(9, m[1])
    self.assertEqual(9, m[6])


def test_extract_recycling_rule():
    # recycling rule
    v = robjects.Vector(array.array('i', range(1, 23)))
    m = robjects.r.matrix(v, ncol = 2)
    col = m.rx(True, 1)
    assert len(col) == 1


def test_extract_list():
    # list
    letters = robjects.baseenv["letters"]
    myList = rlist(l=letters, f="foo")
    idem = robjects.baseenv["identical"]
    assert idem(letters, myList.rx("l")[0])[0]
    assert idem("foo", myList.rx("f")[0])[0]
