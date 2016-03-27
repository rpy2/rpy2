"""
Mapping of the R library "grDevices" for graphical devices
"""

import io, tempfile, os
from contextlib import contextmanager
from rpy2.robjects.packages import importr

grdevices = importr('grDevices')

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
    fn = tempfile.mktemp()
    current = dev_cur()[0]
    try:
        device(fn, *device_args, **device_kwargs)
        yield fn
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
            

