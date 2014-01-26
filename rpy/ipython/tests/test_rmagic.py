import unittest
from itertools import product

import numpy as np
has_pandas = True
try:
    import pandas as pd
except:
    has_pandas = False
from IPython.testing.globalipapp import get_ipython
from IPython.utils.py3compat import PY3

if PY3:
    from io import StringIO
else:
    from StringIO import StringIO

from rpy2.ipython import rmagic
if rmagic.pandas2ri:
    activate = rmagic.pandas2ri.activate
    deactivate = rmagic.pandas2ri.deactivate
elif rmagic.numpy2ri:
    activate = rmagic.numpy2ri.activate
    deactivate = rmagic.numpy2ri.deactivate
else:
    def activate():
        pass
    deactivate = activate

# from IPython.core.getipython import get_ipython
from rpy2 import rinterface

class TestRmagic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        '''Set up an IPython session just once.
        It'd be safer to set it up for each test, but for now, I'm mimicking the
        IPython team's logic.
        '''
        cls.ip = get_ipython()
        # This is just to get a minimally modified version of the changes
        # working
        cls.ip.magic('load_ext rpy2.ipython')

    def setUp(self):
        activate()
    def tearDown(self):
        deactivate()

    def test_push(self):
        rm = rmagic.RMagics(self.ip)
        self.ip.push({'X':np.arange(5), 'Y':np.array([3,5,4,6,7])})
        self.ip.run_line_magic('Rpush', 'X Y')
        np.testing.assert_almost_equal(np.asarray(rm.r('X')), self.ip.user_ns['X'])
        np.testing.assert_almost_equal(np.asarray(rm.r('Y')), self.ip.user_ns['Y'])

    def test_push_localscope(self):
        """Test that Rpush looks for variables in the local scope first."""

        self.ip.run_cell('''
def rmagic_addone(u):
    %Rpush u
    %R result = u+1
    %Rpull result
    return result[0]
u = 0
result = rmagic_addone(12344)
''')
        result = self.ip.user_ns['result']
        np.testing.assert_equal(result, 12345)

    @unittest.skipUnless(has_pandas, 'pandas is not available in python')
    def test_push_dataframe(self):
        rm = rmagic.RMagics(self.ip)
        df = pd.DataFrame([{'a': 1, 'b': 'bar'}, {'a': 5, 'b': 'foo', 'c': 20}])
        self.ip.push({'df':df})
        self.ip.run_line_magic('Rpush', 'df')

        # This is converted to factors, which are currently converted back to Python
        # as integers, so for now we test its representation in R.
        sio = StringIO()
        rinterface.set_writeconsole(sio.write)
        try:
            rm.r('print(df$b[1])')
            self.assertIn('[1] bar', sio.getvalue())
        finally:
            rinterface.set_writeconsole(None)

        # Values come packaged in arrays, so we unbox them to test.
        self.assertEqual(rm.r('df$a[2]')[0], 5)
        missing = rm.r('df$c[1]')[0]
        assert np.isnan(missing), missing

    def test_pull(self):
        rm = rmagic.RMagics(self.ip)
        rm.r('Z=c(11:20)')
        self.ip.run_line_magic('Rpull', 'Z')
        np.testing.assert_almost_equal(np.asarray(rm.r('Z')), self.ip.user_ns['Z'])
        np.testing.assert_almost_equal(self.ip.user_ns['Z'], np.arange(11,21))

    def test_Rconverter(self):
        datapy= np.array([(1, 2.9, 'a'), (2, 3.5, 'b'), (3, 2.1, 'c')], 
            dtype=[('x', '<i4'), ('y', '<f8'), ('z', '|S1')])
        self.ip.user_ns['datapy'] = datapy
        self.ip.run_line_magic('Rpush', 'datapy')

        # test to see if a copy is being made
        v = self.ip.run_line_magic('Rget', '-d datapy')
        w = self.ip.run_line_magic('Rget', '-d datapy')
        np.testing.assert_almost_equal(w['x'], v['x'])
        np.testing.assert_almost_equal(w['y'], v['y'])
        self.assertTrue(np.all(w['z'] == v['z']))
        np.testing.assert_equal(id(w.data), id(v.data))
        self.assertTrue(w.dtype, v.dtype)

        self.ip.run_cell_magic('R', ' -d datar', 'datar=datapy')

        u = self.ip.run_line_magic('Rget', ' -d datar')
        np.testing.assert_almost_equal(u['x'], v['x'])
        np.testing.assert_almost_equal(u['y'], v['y'])
        self.assertTrue(np.all(u['z'] == v['z']))
        np.testing.assert_equal(id(u.data), id(v.data))
        self.assertEqual(u.dtype, v.dtype)


    def test_cell_magic(self):

        self.ip.push({'x':np.arange(5), 'y':np.array([3,5,4,6,7])})
        snippet = '''
        print(summary(a))
        plot(x, y, pch=23, bg='orange', cex=2)
        plot(x, x)
        print(summary(x))
        r = resid(a)
        xc = coef(a)
        '''
        self.ip.run_cell_magic('R', '-i x,y -o r,xc -w 150 -u mm a=lm(y~x)', snippet)
        np.testing.assert_almost_equal(self.ip.user_ns['xc'], [3.2, 0.9])
        np.testing.assert_almost_equal(self.ip.user_ns['r'], np.array([-0.2,  0.9, -1. ,  0.1,  0.2]))


    def test_rmagic_localscope(self):
        self.ip.push({'x':0})
        self.ip.run_line_magic('R', '-i x -o result result <-x+1')
        result = self.ip.user_ns['result']
        self.assertEqual(result[0], 1)

        self.ip.run_cell('''def rmagic_addone(u):
        %R -i u -o result result <- u+1
        return result[0]''')
        self.ip.run_cell('result = rmagic_addone(1)')
        result = self.ip.user_ns['result']
        self.assertEqual(result, 2)

        self.assertRaises(
            NameError,
            self.ip.run_line_magic,
            "R",
            "-i var_not_defined 1+1")

    def test_plotting_args(self):
        self.ip.push({'x':np.arange(5), 'y':np.array([3,5,4,6,7])})

        cell = '''
        plot(x, y, pch=23, bg='orange', cex=2)
        '''
        
        png_px_args = [' '.join(('--units=px',w,h,p)) for 
                       w, h, p in product(['--width=400 ',''],
                                          ['--height=400',''],
                                          ['-p=10', ''])]

        for line in png_px_args:
            self.ip.run_line_magic('Rdevice', 'png')
            yield self.ip.run_cell_magic, 'R', line, cell

        basic_args = [' '.join((w,h,p)) for w, h, p in product(['--width=6 ',''],
                                                               ['--height=6',''],
                                                               ['-p=10', ''])]

        for line in basic_args:
            self.ip.run_line_magic('Rdevice', 'svg')
            yield self.ip.run_cell_magic, 'R', line, cell

        png_args = ['--units=in --res=1 ' + s for s in basic_args]
        for line in png_args:
            self.ip.run_line_magic('Rdevice', 'png')
            yield self.ip.run_cell_magic, 'R', line, cell
