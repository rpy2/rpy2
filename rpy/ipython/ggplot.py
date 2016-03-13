""" Goodies for ipython """

import os
import tempfile
import io
from rpy2 import robjects
from rpy2.robjects.packages import importr
from rpy2.robjects.lib import ggplot2

from IPython.core.display import Image

grdevices = importr('grDevices')

# automatic plotting of ggplot2 figures in the notebook

class GGPlot(ggplot2.GGPlot):

    # special representation for ipython
    def _repr_png_(self, width = 700, height = 500):
        # Hack with a temp file (use buffer later ?)
        fn = tempfile.NamedTemporaryFile(mode = 'wb', suffix = '.png',
                                         delete = False)
        fn.close()
        grdevices.png(fn.name, width = width, height = height)
        self.plot()
        grdevices.dev_off()
        with io.OpenWrapper(fn.name, mode='rb') as data:
           res = data.read()
        return res

    def png(self, width = 700, height = 500):
        """ Build an Ipython "Image" (requires iPython). """
        return Image(self._repr_png_(width = width, height = height), 
                     embed=True)


ggplot = GGPlot.new


class GGPlotSVG(ggplot2.GGPlot):
    """ The embedding of several SVG figures into one ipython notebook is
    giving garbled figures. The SVG functionality is taken out to a
    child class.
    """
    def _repr_svg_(self, width = 6, height = 4):
        # Hack with a temp file (use buffer later ?)
        fn = tempfile.NamedTemporaryFile(mode = 'wb', suffix = '.svg',
                                         delete = False)
        fn.close()
        grdevices.svg(fn.name, width = width, height = height)
        self.plot()
        grdevices.dev_off()
        with io.OpenWrapper(fn.name, mode='rb') as data:
           res = data.read().decode('utf-8')
        return res

    def svg(self, width = 6, height = 4):
        """ Build an Ipython "Image" (requires iPython). """
        return Image(self._repr_svg_(width = width, height = height), 
                     embed=True)


def display_png(gg, width=800, height=400):
    """ Hook to render ggplot2 figures"""
    fn = tempfile.mktemp()
    try:
        robjects.r("png")(fn, type="cairo-png", 
                          width=width, height=height, 
                          antialias="subpixel")
        robjects.r("print")(gg)
        robjects.r("dev.off()")
        b = io.BytesIO()
        with open(fn, 'rb') as fh:
            b.write(fh.read())
    finally:
        if os.path.exists(fn):
            os.unlink(fn)
    data = b.getvalue()
    ip_img = Image(data=data, format='png', embed=True)
    return ip_img._repr_png_()
