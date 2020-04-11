import pytest

from rpy2.robjects import packages

try:
    from rpy2.robjects.lib import ggplot2
    has_ggplot = True
    msg = ''
except packages.PackageNotInstalledError as error:
    has_ggplot = False
    msg = str(error)

datasets = packages.importr('datasets')
mtcars = datasets.__rdata__.fetch('mtcars')['mtcars']

@pytest.mark.skipif(not has_ggplot, reason=msg)
class TestGGplot(object):
    
    def test_gglot(self):
        gp = ggplot2.ggplot(mtcars)
        assert isinstance(gp, ggplot2.GGPlot)

    def test_element_text(self):
        et = ggplot2.element_text()
        assert isinstance(et, ggplot2.ElementText)

    def test_element_text_repr(self):
        et = ggplot2.element_text()
        assert repr(et).startswith('<instance of')

    def test_element_rect(self):
        er = ggplot2.element_rect()
        assert isinstance(er, ggplot2.ElementRect)

    def test_element_blank(self):
        eb = ggplot2.element_blank()
        assert isinstance(eb, ggplot2.ElementBlank)

    def test_labs(self):
        la = ggplot2.labs()
        assert isinstance(la, ggplot2.Labs)

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
        'theme_name',
        ['theme_grey',
         'theme_classic',
         'theme_dark',
         'theme_grey',
         'theme_light',
         'theme_bw',
         'theme_linedraw',
         'theme_void',
         'theme_minimal'])
    def test_theme(self, theme_name):
        theme = getattr(ggplot2, theme_name)
        gp = (ggplot2.ggplot(mtcars) +
              theme())
        assert isinstance(gp, ggplot2.GGPlot)
