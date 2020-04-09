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


def test_mapperR2Python_lang():
    sexp = rinterface.baseenv['str2lang']('1+2')
    ob = robjects.default_converter.rpy2py(sexp)
    assert isinstance(ob, robjects.language.LangVector)


def test_NameClassMap():
    ncm = robjects.conversion.NameClassMap(object)
    classnames = ('A', 'B')
    assert ncm.find_key(classnames) is None
    assert ncm.find(classnames) is object
    ncm['B'] = list
    assert ncm.find_key(classnames) == 'B'
    assert ncm.find(classnames) is list
    ncm['A'] = tuple
    assert ncm.find_key(classnames) == 'A'
    assert ncm.find(classnames) is tuple


def test_NameClassMapContext():
    ncm = robjects.conversion.NameClassMap(object)
    assert not len(ncm._map)
    with robjects.conversion.NameClassMapContext(ncm, {}):
        assert not len(ncm._map)
    assert not len(ncm._map)
    
    with robjects.conversion.NameClassMapContext(ncm, {'A': list}):
        assert set(ncm._map.keys()) == set('A')
    assert not len(ncm._map)
    ncm['B'] = tuple
    with robjects.conversion.NameClassMapContext(ncm, {'A': list}):
        assert set(ncm._map.keys()) == set('AB')
    assert set(ncm._map.keys()) == set('B')
    with robjects.conversion.NameClassMapContext(ncm, {'B': list}):
        assert set(ncm._map.keys()) == set('B')
    assert set(ncm._map.keys()) == set('B')
    assert ncm['B'] is tuple


def test_Converter_rclass_map_context():
    converter = robjects.default_converter

    class FooEnv(robjects.Environment):
        pass

    ncm = converter.rpy2py_nc_name[rinterface.SexpEnvironment]
    with robjects.default_converter.rclass_map_context(
            rinterface.SexpEnvironment, {'A': FooEnv}
    ):
        assert set(ncm._map.keys()) == set('A')
    assert not len(ncm._map)


@pytest.fixture(scope='module')
def _set_class_AB():
    robjects.r('A <- methods::setClass("A", representation(x="integer"))')
    robjects.r('B <- methods::setClass("B", contains="A")')
    yield
    robjects.r('methods::removeClass("B")')
    robjects.r('methods::removeClass("A")')


def test_mapperR2Python_s4(_set_class_AB):
    classname = rinterface.StrSexpVector(['A', ])
    one = rinterface.IntSexpVector([1, ])
    sexp = rinterface.globalenv['A'](x=one)
    assert isinstance(robjects.default_converter.rpy2py(sexp), 
                      robjects.RS4)


def test_mapperR2Python_s4custom(_set_class_AB):
    class A(robjects.RS4):
        pass
    sexp_a = rinterface.globalenv['A']( 
        x=rinterface.IntSexpVector([1, ])
    )
    sexp_b = rinterface.globalenv['B']( 
        x=rinterface.IntSexpVector([2, ])
    )
    rs4_map = robjects.conversion.converter.rpy2py_nc_name[rinterface.SexpS4]
    with robjects.conversion.NameClassMapContext(
            rs4_map,
            {'A': A}
    ):
        assert rs4_map.find_key(('A', )) == 'A'
        assert isinstance(
            robjects.default_converter.rpy2py(sexp_a), 
            A)
        assert rs4_map.find_key(('B', 'A')) == 'A'
        assert isinstance(
            robjects.default_converter.rpy2py(sexp_b), 
            A)

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
