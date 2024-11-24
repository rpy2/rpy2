import array
import pytest
import rpy2.rinterface as rinterface
import rpy2.robjects as robjects

# TODO: what is this ?
# def tearDow(self):
#     robjects.r._dotter = False
        
def test_getitem():
    letters_R = robjects.r['letters']
    assert isinstance(letters_R, robjects.Vector)
    letters = (('a', 0), ('b', 1), ('c', 2), ('x', 23), ('y', 24), ('z', 25))
    for l, i in letters:
        assert letters_R[i] == l

    as_list_R = robjects.r['as.list']
    seq_R = robjects.r['seq']

    mySeq = seq_R(0, 10)

    myList = as_list_R(mySeq)

    for i, li in enumerate(myList):
        assert myList[i][0] == i

        
def test_eval():
    # vector long enough to span across more than one line
    x = robjects.baseenv['seq'](1, 50, 2)
    res = robjects.r('sum(%s)' %x.r_repr())
    assert res[0] == 625


def test_items():
    v = robjects.IntVector((1,2,3))
    rs = robjects.robject.RSlots(v)
    assert len(tuple(rs.items())) == 0

    v.do_slot_assign('a', robjects.IntVector((9,)))
    for ((k_o,v_o), (k,v)) in zip((('a', robjects.IntVector), ), rs.items()):
        assert k_o == k
        assert v_o == type(v)


def test_values():
    v = robjects.IntVector((1,2,3))
    rs = robjects.robject.RSlots(v)
    assert len(tuple(rs.items())) == 0

    v.do_slot_assign('a', robjects.IntVector((9,)))
    for (v_o, v) in zip((robjects.IntVector, ), rs.values()):
        assert v_o == type(v)


def test_init():

    identical = rinterface.baseenv['identical']
    py_a = array.array('i', [1,2,3])
    with pytest.raises(ValueError):
        robjects.RObject(py_a)

    ri_v = rinterface.IntSexpVector(py_a)
    ro_v = robjects.RObject(ri_v)

    assert identical(ro_v, ri_v)[0] is True

    del(ri_v)
    assert rinterface.RTYPES.INTSXP == ro_v.typeof


def test_r_repr():
    obj = robjects.baseenv['pi']
    s = obj.r_repr()
    assert s.startswith('3.14')


def test_str():
    prt = robjects.baseenv['pi']
    s = prt.__str__()
    assert s.startswith('[1] 3.14')


def test_rclass():
    assert robjects.baseenv['letters'].rclass[0] == 'character'
    assert robjects.baseenv['pi'].rclass[0] == 'numeric'
    assert robjects.globalenv.find('help').rclass[0] == 'function'
                      

def test_rclass_set():
    x = robjects.r('1:3')
    old_class = x.rclass
    x.rclass = robjects.StrVector(('Foo', )) + x.rclass
    assert x.rclass[0] == 'Foo'
    assert old_class[0] == x.rclass[1]


def test_rclass_set_usingstring():
    x = robjects.r('1:3')
    old_class = x.rclass
    x.rclass = 'Foo'
    assert x.rclass[0] == 'Foo'


def test_rclass_str():
    s = str(robjects.r)
    assert isinstance(s, str)


def test_do_slot():    
    assert robjects.globalenv.find('BOD').do_slot('reference')[0] == 'A1.4, p. 270'


def test_slots():
    x = robjects.r('list(a=1,b=2,c=3)')
    s = x.slots
    assert len(s) == 1
    assert tuple(s.keys()) == ('names', )
    assert tuple(s['names']) == ('a', 'b', 'c')

    s['names'] = 0
    assert len(s) == 1
    assert tuple(s.keys()) == ('names', )
    assert tuple(s['names']) == (0, )
