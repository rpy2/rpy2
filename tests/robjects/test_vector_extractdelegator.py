import pytest
from rpy2 import robjects
from .. import utils

@pytest.fixture(scope='module')
def silent_console_print():
    with utils.obj_in_module(rinterface.callbacks, 'consolewrite_print', _just_pass):
        yield

    self.console = robjects.rinterface.get_writeconsole_regular()

def tearDown(self):
    robjects.rinterface.set_writeconsole_regular(self.console)


def testFloorDivision(self):
    v = robjects.vectors.IntVector((2,3,4))
    res = v.ro // 2
    self.assertEqual((1,1,2), tuple(int(x) for x in res))

def testExtractByIndex(self):
    seq_R = robjects.baseenv["seq"]
    mySeq = seq_R(0, 10)
    # R indexing starts at one
    myIndex = robjects.Vector(array.array('i', range(1, 11, 2)))

    mySubset = mySeq.rx(myIndex)
    for i, si in enumerate(myIndex):
        self.assertEqual(mySeq[si-1], mySubset[i])

def testExtractByName(self):
    seq_R = robjects.baseenv["seq"]
    mySeq = seq_R(0, 25)

    letters = robjects.baseenv["letters"]
    mySeq = robjects.baseenv["names<-"](mySeq, 
                                                 letters)

    # R indexing starts at one
    myIndex = robjects.Vector(letters[2])

    mySubset = mySeq.rx(myIndex)

    for i, si in enumerate(myIndex):
        self.assertEqual(2, mySubset[i])

def testExtractIndexError(self):
    seq_R = robjects.baseenv["seq"]
    mySeq = seq_R(0, 10)
    # R indexing starts at one
    myIndex = robjects.Vector(['a', 'b', 'c'])

    def noconsole(x):
        pass
    robjects.rinterface.set_writeconsole_regular(noconsole)

    self.assertRaises(ri.RRuntimeError, mySeq.rx, myIndex)



def testReplace(self):
    vec = robjects.IntVector(range(1, 6))
    i = array.array('i', [1, 3])
    vec.rx[rlc.TaggedList((i, ))] = 20
    self.assertEqual(20, vec[0])
    self.assertEqual(2, vec[1])
    self.assertEqual(20, vec[2])
    self.assertEqual(4, vec[3])

    vec = robjects.IntVector(range(1, 6))
    i = array.array('i', [1, 5])
    vec.rx[rlc.TaggedList((i, ))] = 50
    self.assertEqual(50, vec[0])
    self.assertEqual(2, vec[1])
    self.assertEqual(3, vec[2])
    self.assertEqual(4, vec[3])
    self.assertEqual(50, vec[4])

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

def testExtractRecyclingRule(self):
    # recycling rule
    v = robjects.Vector(array.array('i', range(1, 23)))
    m = robjects.r.matrix(v, ncol = 2)
    col = m.rx(True, 1)
    self.assertEqual(11, len(col))

def testExtractList(self):
    # list
    letters = robjects.baseenv["letters"]
    myList = rlist(l=letters, f="foo")
    idem = robjects.baseenv["identical"]
    self.assertTrue(idem(letters, myList.rx("l")[0]))
    self.assertTrue(idem("foo", myList.rx("f")[0]))
