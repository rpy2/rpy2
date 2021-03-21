import pytest
import sys
from rpy2 import robjects
from rpy2 import rinterface
import rpy2.robjects.conversion as conversion
r = robjects.r


class DummyNamespace(object):
    def __getattr__(self, name):
        return None


has_numpy = False
try:
    import numpy
    has_numpy = True
    import rpy2.robjects.numpy2ri as rpyn
except:
    numpy = DummyNamespace()


@pytest.fixture()
def numpy_conversion():
    with conversion.localconverter(
            robjects.default_converter + rpyn.converter
    ) as lc:
        yield


@pytest.mark.skipif(not has_numpy,
                    reason='package numpy cannot be imported')
@pytest.mark.usefixtures('numpy_conversion')
class TestNumpyConversions(object):

    def check_homogeneous(self, obj, mode, storage_mode):
        converted = conversion.py2rpy(obj)
        assert r["mode"](converted)[0] == mode
        assert r["storage.mode"](converted)[0] == storage_mode
        assert list(obj) == list(converted)
        assert r["is.array"](converted)[0] is True
        return converted

    def test_vector_boolean(self):
        l = [True, False, True]
        b = numpy.array(l, dtype=numpy.bool_)
        b_r = self.check_homogeneous(b, "logical", "logical")
        assert tuple(l) == tuple(b_r)

    def test_vector_integer(self):
        l = [1, 2, 3]
        i = numpy.array(l, dtype="i")
        i_r = self.check_homogeneous(i, "numeric", "integer")
        assert tuple(l) == tuple(i_r)
        
    def test_vector_float(self):
        l = [1.0, 2.0, 3.0]
        f = numpy.array(l, dtype="f")
        f_r = self.check_homogeneous(f, "numeric", "double")
        for orig, conv in zip(l, f_r):
            assert abs(orig-conv) < 0.000001
        
    def test_vector_complex(self):
        l = [1j, 2j, 3j]
        c = numpy.array(l, dtype=numpy.complex_)
        c_r = self.check_homogeneous(c, "complex", "complex")
        for orig, conv in zip(l, c_r):
            assert abs(orig.real-conv.real) < 0.000001
            assert abs(orig.imag-conv.imag) < 0.000001

    def test_vector_unicode_character(self):
        l = [u"a", u"c", u"e"]
        u = numpy.array(l, dtype="U")
        u_r = self.check_homogeneous(u, "character", "character")
        assert tuple(l) == tuple(u_r)

    def test_vector_bytes(self):
        l = [b'a', b'b', b'c']
        s = numpy.array(l, dtype = '|S1')
        converted = conversion.py2rpy(s)
        assert r["mode"](converted)[0] == 'raw'
        assert r["storage.mode"](converted)[0] == 'raw'
        assert bytearray(b''.join(l)) == bytearray(converted)

    def test_array(self):

        i2d = numpy.array([[1, 2, 3], [4, 5, 6]], dtype='i')
        i2d_r = conversion.py2rpy(i2d)
        assert r['storage.mode'](i2d_r)[0] == 'integer'
        assert tuple(r['dim'](i2d_r)) == (2, 3)

        # Make sure we got the row/column swap right:
        assert r['['](i2d_r, 1, 2)[0] == i2d[0, 1]

        f3d = numpy.arange(24, dtype='f').reshape((2, 3, 4))
        f3d_r = conversion.py2rpy(f3d)

        assert r['storage.mode'](f3d_r)[0] == 'double'
        assert tuple(r['dim'](f3d_r)) == (2, 3, 4)

        # Make sure we got the row/column swap right:
        #assert r['['](f3d_r, 1, 2, 3)[0] == f3d[0, 1, 2]

    @pytest.mark.skipif(not has_numpy,
                        reason='package numpy cannot be imported')
    @pytest.mark.parametrize(
        'constructor',
        (numpy.int32, numpy.int64,
         numpy.uint32, numpy.uint64)
    )
    def test_scalar_int(self, constructor):
        np_value = constructor(100)
        r_vec = conversion.py2rpy(np_value)
        r_scalar = numpy.array(r_vec)[0]
        assert np_value == r_scalar

    @pytest.mark.skipif(not (has_numpy and hasattr(numpy, 'float128')),
                        reason='numpy.float128 not available on this system')
    def test_scalar_f128(self):
        f128 = numpy.float128(100.000000003)
        f128_r = conversion.py2rpy(f128)
        f128_test = numpy.array(f128_r)[0]
        assert f128 == f128_test

    def test_object_array(self):
        o = numpy.array([1, "a", 3.2], dtype=numpy.object_)
        o_r = conversion.py2rpy(o)
        assert r['mode'](o_r)[0] == 'list'
        assert r['[['](o_r, 1)[0] == 1
        assert r['[['](o_r, 2)[0] == 'a'
        assert r['[['](o_r, 3)[0] == 3.2

    def test_record_array(self):
        rec = numpy.array([(1, 2.3), (2, -0.7), (3, 12.1)],
                          dtype=[("count", "i"), ("value", numpy.double)])
        rec_r = conversion.py2rpy(rec)
        assert r["is.data.frame"](rec_r)[0] is True
        assert tuple(r["names"](rec_r)) == ("count", "value")
        count_r = rec_r[rec_r.names.index('count')]
        value_r = rec_r[rec_r.names.index('value')]
        assert r["storage.mode"](count_r)[0] == 'integer'
        assert r["storage.mode"](value_r)[0] == 'double'
        assert count_r[1] == 2
        assert value_r[2] == 12.1

    def test_bad_array(self):
        u = numpy.array([1, 2, 3], dtype=numpy.uint32)
        with pytest.raises(ValueError):
            conversion.py2rpy(u)

    def test_assign_numpy_object(self):
        x = numpy.arange(-10., 10., 1)
        env = robjects.Environment()
        env['x'] = x
        assert len(env) == 1
        # do have an R object of the right type ?
        with conversion.localconverter(
            robjects.default_converter
        ) as lc:
            x_r = env['x']

        assert robjects.rinterface.RTYPES.REALSXP == x_r.typeof
        #
        assert tuple(x_r.dim) == (20,)


    def test_dataframe_to_numpy(self):
        df = robjects.vectors.DataFrame(
            {'a': 1,
             'b': 2,
             'c': robjects.vectors.FactorVector('e')})
        rec = conversion.rpy2py(df)
        assert numpy.recarray == type(rec)
        assert rec.a[0] == 1
        assert rec.b[0] == 2
        assert rec.c[0] == 'e'

    def test_atomic_vector_to_numpy(self):
        v = robjects.vectors.IntVector((1,2,3))
        a = rpyn.rpy2py(v)
        assert isinstance(a, numpy.ndarray)
        assert v[0] == 1

    def test_rx2(self):
        df = robjects.vectors.DataFrame({
            "A": robjects.vectors.IntVector([1,2,3]),
            "B": robjects.vectors.IntVector([1,2,3])})
        b = df.rx2('B')
        assert tuple((1,2,3)) == tuple(b)

    def test_rint_to_numpy(self):
        a = robjects.r('c(1:4)')
        assert isinstance(a, numpy.ndarray)

    def test_rfloat_to_numpy(self):
        a = robjects.r('c(1.0, 2.0, 3.0)')
        assert isinstance(a, numpy.ndarray)


@pytest.mark.skipif(not has_numpy,
                    reason='package numpy cannot be imported')
@pytest.mark.parametrize('dtype',
                         ('uint32', 'uint64'))
def test_unsignednumpyint_to_rint_error(dtype):
    values = (1,2,3)
    a = numpy.array(values, dtype=dtype)
    with pytest.raises(ValueError):
        rpyn.unsignednumpyint_to_rint(a)


@pytest.mark.skipif(not has_numpy,
                    reason='package numpy cannot be imported')
@pytest.mark.parametrize('dtype',
                         ('uint8', 'uint16'))
def test_unsignednumpyint_to_rint(dtype):
    values = (1,2,3)
    a = numpy.array(values, dtype=dtype)
    v = rpyn.unsignednumpyint_to_rint(a)
    assert values == tuple(v)


@pytest.mark.skipif(not has_numpy,
                    reason='package numpy cannot be imported')
@pytest.mark.parametrize('values,expected_cls',
                         ((['a', 1, 2], robjects.vectors.ListVector),
                          (['a', 'b', 'c'], rinterface.StrSexpVector),
                          ([b'a', b'b', b'c'], rinterface.ByteSexpVector)))
def test_numpy_O_py2rpy(values, expected_cls):
    a = numpy.array(values, dtype='O')
    v = rpyn.numpy_O_py2rpy(a)
    assert isinstance(v, expected_cls)

    
