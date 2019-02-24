import pytest

# Try to load R ggplot package, and see if it works
from rpy2.rinterface_lib.embedded import RRuntimeError
has_ggplot = True
try:
    from rpy2.robjects.lib import ggplot2
except RRuntimeError:
    has_ggplot = False

from rpy2.robjects.packages import importr
datasets = importr('datasets')
mtcars = datasets.__rdata__.fetch('mtcars')['mtcars']

@pytest.mark.skipif(not has_ggplot, reason='R package ggplot is not installed.')
@pytest.mark.lib_ggplot2
class TestGGplot(object):
    
    def test_gglot(self):
        gp = ggplot2.ggplot(mtcars)
        assert isinstance(gp, ggplot2.GGPlot)

    def test_add(self):
        gp = ggplot2.ggplot(mtcars)
        gp += ggplot2.aes_string(x='wt', y='mpg')
        gp += ggplot2.geom_point()
        assert isinstance(gp, ggplot2.GGPlot)

    def test_aes(self):
        gp = ggplot2.ggplot(mtcars)
        gp += ggplot2.aes(x='wt', y='mpg')
        gp += ggplot2.geom_point()
        assert isinstance(gp, ggplot2.GGPlot)

    @pytest.mark.parametrize(
        'theme',
        [ggplot2.theme_grey,
         ggplot2.theme_classic,
         ggplot2.theme_dark,
         ggplot2.theme_light,
         ggplot2.theme_bw,
         ggplot2.theme_linedraw,
         ggplot2.theme_void,
         ggplot2.theme_minimal])
    def test_theme(self, theme):
        gp = (ggplot2.ggplot(mtcars) +
              theme())
        assert isinstance(gp, ggplot2.GGPlot)
