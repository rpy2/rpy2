import array
import pytest
import rpy2.rinterface_lib.sexp
from rpy2 import rinterface
from rpy2 import robjects


def test_mapperR2Python_string():
    sexp = rinterface.globalenv.find('letters')
    ob = robjects.default_converter.rpy2py(sexp)
    assert isinstance(ob, robjects.Vector)


def test_mapperR2Python_boolean():
    sexp = rinterface.globalenv.find('T')
    ob = robjects.default_converter.rpy2py(sexp)
    assert isinstance(ob, robjects.Vector)


def test_mapperR2Python_function():
    sexp = rinterface.globalenv.find('plot')
    ob = robjects.default_converter.rpy2py(sexp)
    assert isinstance(ob, robjects.Function)

    
def test_mapperR2Python_environment():
    sexp = rinterface.globalenv.find('.GlobalEnv')
    assert isinstance(robjects.default_converter.rpy2py(sexp), 
                      robjects.Environment)


def test_mapperR2Python_s4():
    robjects.r('setClass("A", representation(x="integer"))')
    classname = rinterface.StrSexpVector(['A', ])
    one = rinterface.IntSexpVector([1, ])
    sexp = rinterface.globalenv.find('new')(classname, 
                                           x=one)
    assert isinstance(robjects.default_converter.rpy2py(sexp), 
                      robjects.RS4)


@pytest.mark.parametrize('value,cls', [
    (1, int),
    (True, bool),
    (b'houba', bytes),
    (1.0, float),
    (1.0 + 2j, complex)
])
def test_py2ro_mappedtype(value, cls):
    pyobj = value
    assert isinstance(pyobj, cls)
    rob = robjects.default_converter.py2rpy(pyobj)
    assert isinstance(rob, cls)
                    

def test_mapperPy2R_taggedlist():
    py = robjects.rlc.TaggedList(('a', 'b'),
                                 tags=('foo', 'bar'))
    robj = robjects.default_converter.py2rpy(py)
    assert isinstance(robj, robjects.Vector)
    assert len(robj) == 2
    assert tuple(robj.names) == ('foo', 'bar')


def test_mapperPy2R_function():
    func = lambda x: x
    rob = robjects.default_converter.py2rpy(func)
    assert isinstance(rob, robjects.SignatureTranslatedFunction)
    assert rob.typeof == rinterface.RTYPES.CLOSXP


@pytest.mark.parametrize('ctype', ['h', 'H', 'i', 'I'])
def test_mapperpy2rpy_int_array(ctype):
    a = array.array(ctype, range(10))
    rob = robjects.default_converter.py2rpy(a)
    assert isinstance(rob, robjects.vectors.IntSexpVector)
    assert isinstance(rob, robjects.vectors.IntVector)
    assert rob.typeof == rinterface.RTYPES.INTSXP


@pytest.mark.parametrize('ctype', ['d', 'f'])
def test_mapperpy2rpy_float_array(ctype):
    a = array.array(ctype, (1.1, 2.2, 3.3))
    rob = robjects.default_converter.py2rpy(a)
    assert isinstance(rob, robjects.vectors.FloatSexpVector)
    assert isinstance(rob, robjects.vectors.FloatVector)
    assert rob.typeof == rinterface.RTYPES.REALSXP

    
def noconversion():
    robj_res = robjects.baseenv['pi']
    assert isinstance(robj_res, robjects.RObject)
    rint_res = robject.conversion.noconversion(robj_res)
    assert isinstance(rint_res, rpy2.rinterface_lib.sexp.Sexp)
