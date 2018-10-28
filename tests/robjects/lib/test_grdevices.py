import pytest
import contextlib
import os
import tempfile

from rpy2.robjects.packages import importr, data
datasets = importr('datasets')
mtcars = data(datasets).fetch('mtcars')['mtcars']
from rpy2.robjects import r

from rpy2.robjects.lib import grdevices


@contextlib.contextmanager
def set_filenames_to_delete():
    todelete = set()
    yield todelete
    for fn in todelete:
        if os.path.exists(fn):
            os.unlink(fn)


def testRenderToBytesNoPlot(self):
    with grdevices.render_to_bytesio(grdevices.png) as b:
        pass
    self.assertEqual(0, len(b.getvalue()))


def testRenderToFile(self):
    fn = tempfile.mktemp(suffix=".png")
    with set_filenames_to_delete() as todelete:
        todelete.append(fn)
        
        with grdevices.render_to_file(grdevices.png,
                                      filename=fn) as d:
            r(''' plot(0) ''')
        self.assertTrue(os.path.exists(fn))


def testRenderToBytesPlot(self):
    with grdevices.render_to_bytesio(grdevices.png) as b:
        r(''' plot(0) ''')
    self.assertTrue(len(b.getvalue()) > 0)
