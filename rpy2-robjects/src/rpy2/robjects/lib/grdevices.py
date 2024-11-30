"""
Mapping of the R library "grDevices" for graphical devices
"""

import io
import os
import tempfile
from contextlib import contextmanager
from rpy2.robjects.packages import importr, WeakPackage

grdevices = importr('grDevices')

grdevices = WeakPackage(grdevices._env,
                        grdevices.__rname__,
                        translation=grdevices._translation,
                        exported_names=grdevices._exported_names,
                        on_conflict="warn",
                        version=grdevices.__version__,
                        symbol_r2python=grdevices._symbol_r2python,
                        symbol_resolve=grdevices._symbol_resolve)

# non-interactive file devices
png = grdevices.png
jpeg = grdevices.jpeg
bmp = grdevices.bmp
tiff = grdevices.tiff

svg = grdevices.svg

postscript = grdevices.postscript
pdf = grdevices.pdf
cairo_pdf = grdevices.cairo_pdf

#
X11 = grdevices.X11

# OS X
quartz = grdevices.quartz

# devices
dev_list = grdevices.dev_list
dev_cur = grdevices.dev_cur
dev_next = grdevices.dev_next
dev_prev = grdevices.dev_prev
dev_set = grdevices.dev_set
dev_off = grdevices.dev_off


@contextmanager
def render_to_file(device, *device_args, **device_kwargs):
    """
    Context manager that returns a R figures in a file object.

    :param device: an R "device" function. This function is expected
                   to take a filename as its first argument.

    """
    # TODO: better function signature to check that a file name is passed.
    current = dev_cur()[0]
    try:
        device(*device_args, **device_kwargs)
        yield None
    finally:
        if current != dev_cur()[0]:
            dev_off()


@contextmanager
def render_to_bytesio(device, *device_args, **device_kwargs):
    """
    Context manager that returns a R figures in a :class:`io.BytesIO`
    object.

    :param device: an R "device" function. This function is expected
                   to take a filename as its first argument.

    """
    fn = tempfile.mktemp()
    b = io.BytesIO()
    current = dev_cur()[0]
    try:
        device(fn, *device_args, **device_kwargs)
        yield b
    finally:
        if current != dev_cur()[0]:
            dev_off()
        if os.path.exists(fn):
            with open(fn, 'rb') as fh:
                b.write(fh.read())
            os.unlink(fn)
