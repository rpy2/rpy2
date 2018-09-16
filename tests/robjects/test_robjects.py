import pytest
import rpy2.robjects as robjects
rinterface = robjects.rinterface

# TODO: what is this ?
# def tearDow(self):
#     robjects.r._dotter = False
        
def test_getitem():
    letters = robjects.r['letters']
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


def test_mapperR2Python_string():
    sexp = rinterface.globalenv.get('letters')
    ob = robjects.default_converter.ri2ro(sexp)
    assert isinstance(ob, robjects.Vector)


def test_mapperR2Python_boolean():
    sexp = rinterface.globalenv.get('T')
    ob = robjects.default_converter.ri2ro(sexp)
    assert isinstance(ob, robjects.Vector)


def test_mapperR2Python_function():
    sexp = rinterface.globalenv.get('plot')
    ob = robjects.default_converter.ri2ro(sexp)
    assert isinstance(ob, robjects.Function)

    
def test_mapperR2Python_environment():
    sexp = rinterface.globalenv.get('.GlobalEnv')
    assert isinstance(robjects.default_converter.ri2ro(sexp), 
                      robjects.Environment)


def test_mapperR2Python_s4():
    robjects.r('setClass("A", representation(x="integer"))')
    classname = rinterface.StrSexpVector(['A', ])
    one = rinterface.IntSexpVector([1, ])
    sexp = rinterface.globalenv.get('new')(classname, 
                                           x=one)
    assert isinstance(robjects.default_converter.ri2ro(sexp), 
                      robjects.RS4)


def test_mapperPy2R_integer():
    py = 1
    rob = robjects.default_converter.py2ro(py)
    assert isinstance(rob, robjects.Vector)
    assert rob.typeof == rinterface.RTYPES.INTSXP


def test_mapperPy2R_boolean():
    py = True
    rob = robjects.default_converter.py2ro(py)
    assert isinstance(rob, robjects.Vector)
    assert rob.typeof == rinterface.RTYPES.LGLSXP


def test_mapperPy2R_bytes():        
    py = b'houba'
    rob = robjects.default_converter.py2ro(py)
    assert isinstance(rob, robjects.Vector)
    assert rob.typeof == rinterface.RTYPES.STRSXP

    
def test_mapperPy2R_str():
    py = u'houba'
    assert isinstance(py, str)
    rob = robjects.default_converter.py2ro(py)
    assert isinstance(rob, robjects.Vector)
    assert rob.typeof == rinterface.RTYPES.STRSXP
    #FIXME: more tests


def test_mapperPy2R_float():
    py = 1.0
    rob = robjects.default_converter.py2ro(py)
    assert isinstance(rob, robjects.Vector)
    assert rob.typeof == rinterface.RTYPES.REALSXP


def test_mapperPy2R_complex():
    py = 1.0 + 2j
    rob = robjects.default_converter.py2ro(py)
    assert isinstance(rob, robjects.Vector)
    assert rob.typeof == rinterface.RTYPES.CPLXSXP


def test_mapperPy2R_taggedlist(self):
    py = robjects.rlc.TaggedList(('a', 'b'),
                                 tags=('foo', 'bar'))
    robj = robjects.default_converter.py2ro(py)
    assert isinstance(robj, robjects.Vector)
    assert len(robj) == 2
    assert tuple(robj.names) == ('foo', 'bar')


def test_mapperPy2R_function(self):
    func = lambda x: x
    rob = robjects.default_converter.py2ro(func)
    assert isinstance(rob, robjects.SignatureTranslatedFunction)
    assert rob.typeof == rinterface.RTYPES.CLOSXP


def test_override_ri2ro():
    class Density(object):
        def __init__(self, x):
            self._x = x

    def f(obj):
        pyobj = robjects.default_converter.ri2ro(obj)
        inherits = rinterface.baseenv['inherits']
        classname = rinterface.StrSexpVector(['density', ])
                                          
        if inherits(pyobj, classname)[0]:
            pyobj = Density(pyobj)
        return pyobj
    robjects.conversion.ri2ro = f
    x = robjects.r.rnorm(100)
    d = robjects.r.density(x)

    assert isinstance(d, Density)


def test_items():
    v = robjects.IntVector((1,2,3))
    rs = robjects.robject.RSlots(v)
    assert len(tuple(rs.items())) == 0

    v.do_slot_assign("a", robjects.IntVector((9,)))
    for ((k_o,v_o), (k,v)) in zip((("a", robjects.IntVector), ), rs.items()):
        assert k_o == k
        assert v_o == type(v)
            
