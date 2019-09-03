import pytest
from rpy2.robjects.vectors import DataFrame
import rpy2.robjects.lib.ggplot2
from rpy2.ipython import ggplot


def test_image_png():
    dataf = DataFrame({'x': 1, 'Y': 2})
    g = rpy2.robjects.lib.ggplot2.ggplot(dataf)
    img = ggplot.image_png(g)
    assert img
