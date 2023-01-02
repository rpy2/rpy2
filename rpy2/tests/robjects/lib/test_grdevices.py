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


@pytest.mark.xfail(os.name == 'nt',
                   reason='Windows produces non-empty file with no plot')
def test_rendertobytes_noplot():
    with grdevices.render_to_bytesio(grdevices.png) as b:
        pass
    assert len(b.getvalue()) == 0


def test_rendertofile():
    fn = tempfile.mktemp(suffix=".png")
    with set_filenames_to_delete() as todelete:
        todelete.add(fn)
        
        with grdevices.render_to_file(grdevices.png,
                                      filename=fn) as d:
            r(''' plot(0) ''')
        assert os.path.exists(fn)


def test_rendertobytes_plot():
    with grdevices.render_to_bytesio(grdevices.png) as b:
        r(''' plot(0) ''')
    assert len(b.getvalue()) > 0
