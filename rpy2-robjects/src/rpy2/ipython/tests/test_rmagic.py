import pytest
import textwrap
import types
import warnings
from itertools import product
import rpy2.rinterface_lib.callbacks
import rpy2.rinterface_lib._rinterface_capi
import rpy2.robjects
import rpy2.robjects.conversion
from rpy2.rinterface.tests import utils

try:
    import IPython
except ModuleNotFoundError as no_ipython:
    warnings.warn(str(no_ipython))
    IPython = None

if IPython is None:
    rmagic = None
    get_ipython = None
else:
    from rpy2.ipython import rmagic
    from IPython.testing.globalipapp import get_ipython

from io import StringIO

# from IPython.core.getipython import get_ipython
from rpy2 import rinterface
from rpy2.robjects import r, vectors, globalenv
import rpy2.robjects.packages as rpacks

np_string_type = 'U'


@pytest.mark.parametrize(
    'name, devices_dict',
    [
        ('png', {'png': rmagic.graphics_devices['grDevices::png']}),
        ('foo', {'png': rmagic.graphics_devices['grDevices::png'],
                 'foo': ('png', )}),
        ('foo',
         {'png': rmagic.graphics_devices['grDevices::png'],
          'dummy': rmagic.GraphicsDeviceRaster('dummy', 'dummy', 'txt', None),
          'foo': ('dummy', 'png')})
    ]
)
def test_get_valid_device(name, devices_dict):
    name, device = rmagic.get_valid_device(name,
                                           devices_dict=devices_dict)
    assert isinstance(device, rmagic.GraphicsDevice)


@pytest.mark.parametrize(
    'name, devices_dict, error',
    [
        ('foo', {},
         KeyError),
        ('dummy', {
            'dummy': rmagic.GraphicsDeviceRaster(
                'dummy', 'dummy', 'txt', None
            ),
        }, rpacks.LibraryError),
    ]
)
def test_get_valid_device_invalid(name, devices_dict, error):
    with pytest.raises(error):
        rmagic.get_valid_device(name, devices_dict=devices_dict)


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
@pytest.fixture(scope='module')
def clean_globalenv():
    yield
    for name in rinterface.globalenv.keys():
        del rinterface.globalenv[name]


@pytest.fixture(scope='module')
def ipython_with_magic():
    if IPython is None:
        return None
    ip = get_ipython()
    # This is just to get a minimally modified version of the changes
    # working
    ip.run_line_magic('load_ext', 'rpy2.ipython')
    return ip


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
def test_RInterpreterError():
    line = 123
    err = 'Arrh!'
    stdout = 'Kaput'
    rie = rmagic.RInterpreterError(line,
                                   err,
                                   stdout)
    assert str(rie).startswith(
        rie.msg_prefix_template.format(line=line, msg=err)
    )


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
@pytest.mark.parametrize(
    'arg,expected',
    (
        ('foo', ('foo', 'foo')),
        ('bar=foo', ('bar', 'foo')),
        ('bar=baz.foo', ('bar', 'baz.foo'))
    )
)
def test__parse_assignment_argument(arg, expected):
    assert expected == rmagic._parse_assignment_argument(arg)


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
@pytest.mark.skipif(not rmagic.NUMPY_IMPORTED, reason='numpy not installed')
def test_push(ipython_with_magic, clean_globalenv):
    for obj in (rmagic.numpy.arange(5), [1, 2]):
        ipython_with_magic.push({'X': obj})
        ipython_with_magic.run_line_magic('Rpush', 'X')
        rmagic.numpy.testing.assert_almost_equal(
            rmagic.numpy.asarray(r('X')),
            ipython_with_magic.user_ns['X']
        )


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
@pytest.mark.skipif(not rmagic.NUMPY_IMPORTED, reason='numpy not installed')
def test_push_localscope(ipython_with_magic, clean_globalenv):
    """Test that Rpush looks for variables in the local scope first."""
    ipython_with_magic.run_cell(
        textwrap.dedent(
            """
            def rmagic_addone(u):
                %Rpush u
                %R result = u+1
                %Rpull result
                return result[0]
            u = 0
            result = rmagic_addone(12344)
            """)
        )
    result = ipython_with_magic.user_ns['result']
    rmagic.numpy.testing.assert_equal(result, 12345)


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
@pytest.mark.parametrize(
    'rcode,exception_expr',
    (('"a" + 1', 'rmagic.RInterpreterError'),
     ('"a" + ', 'rpy2.rinterface_lib._rinterface_capi.RParsingError'))
)
def test_run_cell_with_error(ipython_with_magic, clean_globalenv,
                             rcode, exception_expr):
    """Run an R block with an error."""

    with pytest.raises(eval(exception_expr)):
        ipython_with_magic.run_line_magic('R', rcode)


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
@pytest.mark.skipif(not rmagic.PANDAS_IMPORTED,
                    reason='pandas is not available in python')
@pytest.mark.skipif(not rmagic.NUMPY_IMPORTED, reason='numpy not installed')
def test_push_dataframe(ipython_with_magic, clean_globalenv):
    df = rmagic.pandas.DataFrame([{'a': 1, 'b': 'bar'},
                                  {'a': 5, 'b': 'foo', 'c': 20}])
    ipython_with_magic.push({'df': df})
    ipython_with_magic.run_line_magic('Rpush', 'df')

    # This is converted to factors, which are currently converted back to
    # Python as integers, so for now we test its representation in R.
    sio = StringIO()
    with utils.obj_in_module(
            rpy2.rinterface_lib.callbacks,
            'consolewrite_print', sio.write
    ):
        r('print(df$b[1])')
        assert '[1] "bar"' in sio.getvalue()

    # Values come packaged in arrays, so we unbox them to test.
    assert r('df$a[2]')[0] == 5
    missing = r('df$c[1]')[0]
    assert rmagic.numpy.isnan(missing), missing


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
@pytest.mark.skipif(not rmagic.NUMPY_IMPORTED, reason='numpy not installed')
def test_pull(ipython_with_magic, clean_globalenv):
    r('Z=c(11:20)')
    ipython_with_magic.run_line_magic('Rpull', 'Z')
    rmagic.numpy.testing.assert_almost_equal(rmagic.numpy.asarray(r('Z')),
                                             ipython_with_magic.user_ns['Z'])
    rmagic.numpy.testing.assert_almost_equal(ipython_with_magic.user_ns['Z'],
                                             rmagic.numpy.arange(11, 21))


def _test_Rconverter(ipython_with_magic, clean_globalenv,
                     dataf_py, cls):
    # If we get to dropping numpy requirement, we might use something
    # like the following:
    # assert tuple(buffer(a).buffer_info()) == tuple(buffer(b).buffer_info())

    # store it in the notebook's user namespace
    ipython_with_magic.user_ns['dataf_py'] = dataf_py

    # equivalent to:
    #     %Rpush dataf_np
    # that is send Python object 'dataf_py' into R's globalenv
    # as 'dataf_r'. The current conversion rules should make it an
    # R data frame.
    ipython_with_magic.run_line_magic('Rpush', 'dataf_py')

    # Now retreive 'dataf_py' from R's globalenv. Twice because
    # we want to test whether copies are made
    fromr_dataf_py = ipython_with_magic.run_line_magic(
        'Rget', 'dataf_py'
    )
    fromr_dataf_py_again = ipython_with_magic.run_line_magic(
        'Rget', 'dataf_py'
    )

    assert isinstance(fromr_dataf_py, cls)
    assert len(dataf_py) == len(fromr_dataf_py)
    assert len(dataf_py) == len(fromr_dataf_py_again)

    # retrieve `dataf_py` from R into `fromr_dataf_py` in the notebook.
    ipython_with_magic.run_cell_magic('R',
                                      '-o dataf_py',
                                      'dataf_py')

    dataf_py_roundtrip = ipython_with_magic.user_ns['dataf_py']
    assert tuple(fromr_dataf_py['x']) == tuple(dataf_py_roundtrip['x'])
    assert tuple(fromr_dataf_py['y']) == tuple(dataf_py_roundtrip['y'])


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
@pytest.mark.skipif(rmagic.PANDAS_IMPORTED or (not rmagic.NUMPY_IMPORTED),
                    reason='numpy not installed')
def test_Rconverter_numpy(ipython_with_magic, clean_globalenv):
    # If we get to dropping numpy requirement, we might use something
    # like the following:
    # assert tuple(buffer(a).buffer_info()) == tuple(buffer(b).buffer_info())

    # numpy recarray (numpy's version of a data frame)
    dataf_np = rmagic.numpy.array(
        [(1, 2.9, 'a'), (2, 3.5, 'b'), (3, 2.1, 'c')],
        dtype=[('x', '<i4'),
               ('y', '<f8'),
               ('z', '|%s1' % np_string_type)]
    )
    _test_Rconverter(
        ipython_with_magic, clean_globalenv,
        dataf_np, rmagic.numpyndarray
    )


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
@pytest.mark.skipif(not rmagic.PANDAS_IMPORTED, reason='pandas not installed')
@pytest.mark.parametrize(
    'python_obj_code,r_cls',
    (
        ("""
rmagic.pandas.DataFrame.from_dict(
  {
    'x': (1, 2, 3),
    'y': (2.9, 3.5, 2.1),
    'z': ('a', 'b', 'c')
  }
)""",
         ('data.frame', )),
        ("""
rmagic.pandas.Categorical.from_codes(
  [0, 1, 0],
  categories=['a', 'b'],
  ordered=False
)""",
         ('factor', ))
    )
)
def test_converter_pandas_py2rpy(
        ipython_with_magic, clean_globalenv,
        python_obj_code, r_cls
):
    py_obj = eval(python_obj_code)
    # If we get to dropping numpy requirement, we might use something
    # like the following:
    # assert tuple(buffer(a).buffer_info()) == tuple(buffer(b).buffer_info())

    # store it in the notebook's user namespace
    ipython_with_magic.user_ns['py_obj'] = py_obj

    # equivalent to:
    #     %Rpush dataf_np
    # that is send Python object 'dataf_py' into R's globalenv
    # as 'dataf_r'. The current conversion rules should make it an
    # R data frame.
    ipython_with_magic.run_line_magic('Rpush', 'py_obj')

    assert tuple(rpy2.robjects.r('class(py_obj)')) == r_cls


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
@pytest.mark.skipif(not rmagic.PANDAS_IMPORTED, reason='pandas not installed')
@pytest.mark.parametrize(
    'r_obj_code,py_cls',
    (
        ("""
data.frame(
  x = c(1, 2, 3),
  y = c(2.9, 3.5, 2.1),
  z = c('a', 'b', 'c')
)""", 'rmagic.pandas.DataFrame'),
        ("""
factor(c('a', 'b', 'a'),
       ordered = TRUE)
""", 'rmagic.pandas.Categorical')
    )
)
def test_converter_pandas_rpy2py(
        ipython_with_magic, clean_globalenv,
        r_obj_code, py_cls
):
    rpy2.robjects.r(f'r_obj <- {r_obj_code}')
    # retrieve `dataf_py` from R into `fromr_dataf_py` in the notebook.
    py_obj = ipython_with_magic.run_line_magic(
        'Rget', 'r_obj'
    )
    assert isinstance(py_obj, eval(py_cls))


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
@pytest.mark.skipif(not rmagic.NUMPY_IMPORTED, reason='numpy not installed')
def test_cell_magic(ipython_with_magic, clean_globalenv):
    ipython_with_magic.push({'x': rmagic.numpy.arange(5),
                             'y': rmagic.numpy.array([3, 5, 4, 6, 7])})
    # For now, print statements are commented out because they print
    # erroneous ERRORs when running via rpy2.tests
    snippet = textwrap.dedent("""
    print(summary(a))
    plot(x, y, pch=23, bg='orange', cex=2)
    plot(x, x)
    print(summary(x))
    r = resid(a)
    xc = coef(a)
    """)
    ipython_with_magic.run_cell_magic(
        'R',
        '-i x,y -o r,xc -w 150 -u mm a=lm(y~x)',
        snippet)
    rmagic.numpy.testing.assert_almost_equal(
        ipython_with_magic.user_ns['xc'],
        [3.2, 0.9]
    )
    rmagic.numpy.testing.assert_almost_equal(
        ipython_with_magic.user_ns['r'],
        rmagic.numpy.array([-0.2, 0.9, -1., 0.1, 0.2])
    )


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
def test_cell_magic_localconverter(ipython_with_magic, clean_globalenv):
    x = (1, 2, 3)
    from rpy2.rinterface import IntSexpVector

    def tuple_str(tpl):
        res = IntSexpVector(tpl)
        return res
    from rpy2.robjects.conversion import Converter
    my_converter = Converter('my converter')
    my_converter.py2rpy.register(tuple, tuple_str)
    from rpy2.robjects import default_converter

    foo = default_converter + my_converter

    snippet = textwrap.dedent("""
    x
    """)

    # Missing converter/object with the specified name.
    ipython_with_magic.push({'x': x})
    with pytest.raises(NameError):
        ipython_with_magic.run_cell_magic('R', '-i x -c foo',
                                          snippet)

    # Converter/object is not a converter.
    ipython_with_magic.push({'x': x,
                             'foo': 123})
    with pytest.raises(TypeError):
        ipython_with_magic.run_cell_magic('R', '-i x -c foo',
                                          snippet)

    ipython_with_magic.push({'x': x,
                             'foo': foo})
    with pytest.raises(NotImplementedError):
        ipython_with_magic.run_cell_magic('R', '-i x', snippet)

    ipython_with_magic.run_cell_magic('R', '-i x -c foo',
                                      snippet)

    # converter in a namespace.
    ns = types.SimpleNamespace()
    ipython_with_magic.push({'x': x,
                             'ns': ns})
    with pytest.raises(AttributeError):
        ipython_with_magic.run_cell_magic('R', '-i x -c ns.bar',
                                          snippet)
    ns.bar = foo
    ipython_with_magic.run_cell_magic('R', '-i x -c ns.bar',
                                      snippet)

    assert isinstance(globalenv['x'], vectors.IntVector)


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
def test_rmagic_localscope(ipython_with_magic, clean_globalenv):
    ipython_with_magic.push({'x': 0})
    ipython_with_magic.run_line_magic('R', '-i x -o result result <-x+1')
    result = ipython_with_magic.user_ns['result']
    assert result[0] == 1

    ipython_with_magic.run_cell(
        textwrap.dedent("""
        def rmagic_addone(u):
            %R -i u -o result result <- u+1
            return result[0]
        """)
    )
    ipython_with_magic.run_cell('result = rmagic_addone(1)')
    result = ipython_with_magic.user_ns['result']
    assert result == 2

    with pytest.raises(NameError):
        ipython_with_magic.run_line_magic(
            "R",
            "-i var_not_defined 1+1")


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
# TODO: There is no test here...
@pytest.mark.skipif(not rmagic.NUMPY_IMPORTED, reason='numpy not installed')
def test_png_plotting_args(ipython_with_magic, clean_globalenv):
    '''Exercise the PNG plotting machinery'''

    ipython_with_magic.push({'x': rmagic.numpy.arange(5),
                             'y': rmagic.numpy.array([3, 5, 4, 6, 7])})

    cell = '''
    plot(x, y, pch=23, bg='orange', cex=2)
    '''

    png_px_args = [' '.join(('--input=x,y --units=px', w, h, p)) for
                   w, h, p in product(['--width=400 ', ''],
                                      ['--height=400', ''],
                                      ['-p=10', ''])]

    for line in png_px_args:
        ipython_with_magic.run_line_magic('Rdevice', 'png')
        ipython_with_magic.run_cell_magic('R', line, cell)


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
def test_display_args(ipython_with_magic, clean_globalenv):

    cell = '''
    x <- 123
    as.integer(x + 1)
    '''

    res = []

    def display(x, a):
        res.append(x)

    with pytest.raises(NameError):
        ipython_with_magic.run_cell_magic('R', '--display=mydisplay', cell)

    ipython_with_magic.push(
        {'mydisplay': display}
    )

    ipython_with_magic.run_cell_magic('R', '--display=mydisplay', cell)
    assert len(res) == 1
    assert tuple(res[0]) == (124,)


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
# TODO: There is no test here...
@pytest.mark.skipif(not rmagic.NUMPY_IMPORTED, reason='numpy not installed')
@pytest.mark.skipif(not rpacks.isinstalled('Cairo'),
                    reason='R package "Cairo" not installed')
def test_svg_plotting_args(ipython_with_magic, clean_globalenv):
    '''Exercise the plotting machinery

    To pass SVG tests, we need Cairo installed in R.'''
    ipython_with_magic.push({'x': rmagic.numpy.arange(5),
                             'y': rmagic.numpy.array([3, 5, 4, 6, 7])})

    cell = textwrap.dedent("""
    plot(x, y, pch=23, bg='orange', cex=2)
    """)

    basic_args = [
        ' '.join((w, h, p))
        for w, h, p in product(['--width=6 ', ''],
                               ['--height=6', ''],
                               ['-p=10', ''])
    ]

    for line in basic_args:
        ipython_with_magic.run_line_magic('Rdevice', 'svg')
        ipython_with_magic.run_cell_magic('R', line + ' --input=x,y', cell)

    png_args = ['--units=in --res=1 ' + s for s in basic_args]
    for line in png_args:
        ipython_with_magic.run_line_magic('Rdevice', 'png')
        ipython_with_magic.run_cell_magic('R', line, cell)


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
@pytest.mark.skipif(not rmagic.NUMPY_IMPORTED, reason='numpy not installed')
@pytest.mark.skip(reason='Test for X11 skipped.')
def test_plotting_X11(ipython_with_magic, clean_globalenv):
    ipython_with_magic.push({'x': rmagic.numpy.arange(5),
                             'y': rmagic.numpy.array([3, 5, 4, 6, 7])})

    cell = textwrap.dedent("""
    plot(x, y, pch=23, bg='orange', cex=2)
    """)
    ipython_with_magic.run_line_magic('Rdevice', 'X11')
    ipython_with_magic.run_cell_magic('R', '', cell)
