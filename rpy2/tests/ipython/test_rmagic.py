import pytest
import textwrap
import warnings
from itertools import product
import rpy2.rinterface_lib.callbacks
from .. import utils

# Currently numpy is a testing requirement, but rpy2 should work without numpy
try:
    import numpy as np
    has_numpy = True
except:
    has_numpy = False
try:
    import pandas as pd
    has_pandas = True
except:
    has_pandas = False

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
np_string_type = 'U'

# from IPython.core.getipython import get_ipython
from rpy2 import rinterface
from rpy2.robjects import r, vectors, globalenv
import rpy2.robjects.packages as rpacks


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
    ip.magic('load_ext rpy2.ipython')
    return ip


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
@pytest.fixture(scope='function')
def set_conversion(ipython_with_magic):
    if hasattr(rmagic.template_converter, 'activate'):
        rmagic.template_converter.activate()
    yield ipython_with_magic
    
    # This seems like the safest thing to return to a safe state
    ipython_with_magic.run_line_magic('Rdevice', 'png')
    if hasattr(rmagic.template_converter, 'deactivate'):
        rmagic.template_converter.deactivate()


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
def test_RInterpreterError():
    line = 123
    err = 'Arrh!'
    stdout = 'Kaput'
    rie = rmagic.RInterpreterError(line,
                                   err,
                                   stdout)
    assert str(rie).startswith(rie.msg_prefix_template % (line, err))


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
@pytest.mark.skipif(not has_numpy, reason='numpy not installed')
def test_push(ipython_with_magic, clean_globalenv):
    ipython_with_magic.push({'X':np.arange(5), 'Y':np.array([3,5,4,6,7])})
    ipython_with_magic.run_line_magic('Rpush', 'X Y')
    np.testing.assert_almost_equal(np.asarray(r('X')),
                                   ipython_with_magic.user_ns['X'])
    np.testing.assert_almost_equal(np.asarray(r('Y')),
                                   ipython_with_magic.user_ns['Y'])


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
@pytest.mark.skipif(not has_numpy, reason='numpy not installed')
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
    np.testing.assert_equal(result, 12345)


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
def test_run_cell_with_error(ipython_with_magic, clean_globalenv):
    """Run an R block with an error."""

    with pytest.raises(rmagic.RInterpreterError):
        ipython_with_magic.run_line_magic('R', '"a" + 1')


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
@pytest.mark.skipif(not has_pandas, reason='pandas is not available in python')
@pytest.mark.skipif(not has_numpy, reason='numpy not installed')
def test_push_dataframe(ipython_with_magic, clean_globalenv):
    df = pd.DataFrame([{'a': 1, 'b': 'bar'}, {'a': 5, 'b': 'foo', 'c': 20}])
    ipython_with_magic.push({'df':df})
    ipython_with_magic.run_line_magic('Rpush', 'df')

    # This is converted to factors, which are currently converted back to Python
    # as integers, so for now we test its representation in R.
    sio = StringIO()
    with utils.obj_in_module(rpy2.rinterface_lib.callbacks,
                             'consolewrite_print', sio.write):
        r('print(df$b[1])')
        assert '[1] "bar"' in sio.getvalue()

    # Values come packaged in arrays, so we unbox them to test.
    assert r('df$a[2]')[0] == 5
    missing = r('df$c[1]')[0]
    assert np.isnan(missing), missing


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
@pytest.mark.skipif(not has_numpy, reason='numpy not installed')
def test_pull(ipython_with_magic, clean_globalenv):
    r('Z=c(11:20)')
    ipython_with_magic.run_line_magic('Rpull', 'Z')
    np.testing.assert_almost_equal(np.asarray(r('Z')),
                                   ipython_with_magic.user_ns['Z'])
    np.testing.assert_almost_equal(ipython_with_magic.user_ns['Z'],
                                   np.arange(11,21))


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
@pytest.mark.skipif(not has_numpy, reason='numpy not installed')
def test_Rconverter(ipython_with_magic, clean_globalenv):
    # If we get to dropping numpy requirement, we might use something
    # like the following:
    # assert tuple(buffer(a).buffer_info()) == tuple(buffer(b).buffer_info())

    # numpy recarray (numpy's version of a data frame)
    dataf_np= np.array([(1, 2.9, 'a'), (2, 3.5, 'b'), (3, 2.1, 'c')],
                       dtype=[('x', '<i4'),
                              ('y', '<f8'),
                              ('z', '|%s1' % np_string_type)])
    # store it in the notebook's user namespace
    ipython_with_magic.user_ns['dataf_np'] = dataf_np
    # equivalent to:
    #     %Rpush dataf_np
    # that is send Python object 'dataf_np' into R's globalenv
    # as 'dataf_np'. The current conversion rules will make it an
    # R data frame.
    ipython_with_magic.run_line_magic('Rpush', 'dataf_np')

    # Now retreive 'dataf_np' from R's globalenv. Twice because
    # we want to test whether copies are made
    fromr_dataf_np = ipython_with_magic.run_line_magic('Rget', 'dataf_np')
    fromr_dataf_np_again = ipython_with_magic.run_line_magic('Rget', 'dataf_np')

    # check whether the data frame retrieved has the same content
    # as the original recarray
    assert len(dataf_np) == len(fromr_dataf_np)
    for col_i, col_n in enumerate(('x', 'y')):
        if has_pandas:
            assert isinstance(fromr_dataf_np, pd.DataFrame)
            assert tuple(dataf_np[col_i]) == tuple(fromr_dataf_np.iloc[col_i].values)
        else:
            # has_numpy then
            assert tuple(dataf_np[col_i]) == tuple(fromr_dataf_np[col_i])

    # pandas2ri is currently making copies
    # # modify the data frame retrieved to check whether
    # # a copy was made
    # fromr_dataf_np['x'].values[0] = 11
    # assert fromr_dataf_np_again['x'][0] == 11
    # fromr_dataf_np['x'].values[0] = 1

    # retrieve `dataf_np` from R into `fromr_dataf_np` in the notebook. 
    ipython_with_magic.run_cell_magic('R',
                                      '-o dataf_np',
                                      'dataf_np')

    dataf_np_roundtrip = ipython_with_magic.user_ns['dataf_np']
    assert tuple(fromr_dataf_np['x']) == tuple(dataf_np_roundtrip['x'])
    assert tuple(fromr_dataf_np['y']) == tuple(dataf_np_roundtrip['y'])


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
@pytest.mark.skipif(not has_numpy, reason='numpy not installed')
def test_cell_magic(ipython_with_magic, clean_globalenv):
    ipython_with_magic.push({'x': np.arange(5), 'y': np.array([3,5,4,6,7])})
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
    ipython_with_magic.run_cell_magic('R', '-i x,y -o r,xc -w 150 -u mm a=lm(y~x)',
                                      snippet)
    np.testing.assert_almost_equal(ipython_with_magic.user_ns['xc'], [3.2, 0.9])
    np.testing.assert_almost_equal(ipython_with_magic.user_ns['r'], np.array([-0.2,  0.9, -1. ,  0.1,  0.2]))


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
def test_cell_magic_localconverter(ipython_with_magic, clean_globalenv):
    x = (1,2,3)
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
    ipython_with_magic.push({'x':x})
    with pytest.raises(NameError):
        ipython_with_magic.run_cell_magic('R', '-i x -c foo',
                                          snippet)

    # Converter/object is not a converter.
    ipython_with_magic.push({'x':x,
                             'foo': 123})
    with pytest.raises(TypeError):
        ipython_with_magic.run_cell_magic('R', '-i x -c foo',
                                          snippet)

    ipython_with_magic.push({'x':x,
                             'foo': foo})

    with pytest.raises(NotImplementedError):
        ipython_with_magic.run_cell_magic('R', '-i x', snippet)

    ipython_with_magic.run_cell_magic('R', '-i x -c foo',
                                      snippet)

    assert isinstance(globalenv['x'], vectors.IntVector)


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
def test_rmagic_localscope(ipython_with_magic, clean_globalenv):
    ipython_with_magic.push({'x':0})
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
@pytest.mark.skipif(not has_numpy, reason='numpy not installed')
def test_png_plotting_args(ipython_with_magic, clean_globalenv):
    '''Exercise the PNG plotting machinery'''

    ipython_with_magic.push({'x':np.arange(5), 'y':np.array([3,5,4,6,7])})

    cell = '''
    plot(x, y, pch=23, bg='orange', cex=2)
    '''

    png_px_args = [' '.join(('--input=x,y --units=px',w,h,p)) for
                   w, h, p in product(['--width=400 ',''],
                                      ['--height=400',''],
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
@pytest.mark.skipif(not has_numpy, reason='numpy not installed')
@pytest.mark.skipif(not rpacks.isinstalled('Cairo'),
                    reason='R package "Cairo" not installed')
def test_svg_plotting_args(ipython_with_magic, clean_globalenv):
    '''Exercise the plotting machinery

    To pass SVG tests, we need Cairo installed in R.'''
    ipython_with_magic.push({'x':np.arange(5), 'y':np.array([3,5,4,6,7])})

    cell = textwrap.dedent("""
    plot(x, y, pch=23, bg='orange', cex=2)
    """)

    basic_args = [' '.join((w,h,p)) for w, h, p in product(['--width=6 ',''],
                                                           ['--height=6',''],
                                                           ['-p=10', ''])]

    for line in basic_args:
        ipython_with_magic.run_line_magic('Rdevice', 'svg')
        ipython_with_magic.run_cell_magic('R', line, cell)

    png_args = ['--units=in --res=1 ' + s for s in basic_args]
    for line in png_args:
        ipython_with_magic.run_line_magic('Rdevice', 'png')
        ipython_with_magic.run_cell_magic('R', line, cell)


@pytest.mark.skipif(IPython is None,
                    reason='The optional package IPython cannot be imported.')
@pytest.mark.skipif(not has_numpy, reason='numpy not installed')
@pytest.mark.skip(reason='Test for X11 skipped.')
def test_plotting_X11(ipython_with_magic, clean_globalenv):
    ipython_with_magic.push({'x':np.arange(5), 'y':np.array([3,5,4,6,7])})

    cell = textwrap.dedent("""
    plot(x, y, pch=23, bg='orange', cex=2)
    """)
    ipython_with_magic.run_line_magic('Rdevice', 'X11')
    ipython_with_magic.run_cell_magic('R', '', cell)
