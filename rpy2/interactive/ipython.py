""" Goodies for ipython """

from rpy2 import robjects
from rpy2.robjects.packages import importr
from rpy2.robjects.lib import ggplot2

from IPython.core.display import Image

import tempfile

grdevices = importr('grDevices')

# automatic plotting of ggplot2 figures

class GGPlot(ggplot2.GGPlot):

    # special representation for ipython
    def _repr_png_(self, width = 800, height = 600):
        # Hack with a temp file (use buffer later ?)
        fn = tempfile.NamedTemporaryFile(mode = 'w', suffix = '.png',
                                         delete = False)

        grdevices.png(fn, width = width, height = height)
        self.plot()
        grdevices.dev_off()
        import io
        with io.OpenWrapper(fn, mode='rb') as data:
           res = data.read()
        return res

    def _repr_svg_(self, width = 7, height = 5):
        # Hack with a temp file (use buffer later ?)
        fn = tempfile.NamedTemporaryFile(mode = 'w', suffix = '.svg',
                                         delete = False)
        grdevices.svg(fn, width = width, height = height)
        self.plot()
        grdevices.dev_off()
        import io
        with io.OpenWrapper(fn, mode='rb') as data:
           res = data.read()
        return res

    def png(self, width = 800, height = 600):
        """ Build an Ipython "Image" (requires iPython). """
        return Image(self._repr_png_(width = width, height = height), 
                     embed=True)

    def svg(self, width = 7, height = 5):
        """ Build an Ipython "Image" (requires iPython). """
        return Image(self._repr_svg_(width = width, height = height), 
                     embed=True)


