import pytest
from rpy2 import rinterface
from rpy2 import robjects


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
