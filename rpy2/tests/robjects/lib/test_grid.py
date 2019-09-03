import pytest
import contextlib
import os
import tempfile

from rpy2.robjects.lib import grid
from rpy2.robjects.vectors import FloatVector, StrVector


# TODO: is there anything to test ?
def test_unit():
    u = grid.unit(1, 'cm')
    u = grid.unit(x=1, units='cm')


# TODO: is there anything to test ?
def test_gpar():
    g = grid.gpar(col='blue')


# TODO: is there anything to test ?
def test_grob():
    g = grid.grob(name='foo')


# TODO: is there anything to test ?
def test_rect():
    r = grid.rect(x=grid.unit(0, 'cm'))


# TODO: is there anything to test ?
def test_lines():
    l = grid.lines(x=grid.unit(FloatVector([0, 1]), 'cm'))


# TODO: is there anything to test ?
def test_circle():
    c = grid.circle(x=0)


# TODO: is there anything to test ?
def test_points():
    c = grid.points()


# TODO: is there anything to test ?
def test_text():
    t = grid.text('t0')


# TODO: is there anything to test ?
def test_gtree():
    g = grid.GTree.gtree()


# TODO: is there anything to test ?
def test_grobtree():
    g = grid.GTree.grobtree()


# TODO: is there anything to test ?
@pytest.mark.parametrize('axis', (grid.XAxis.xaxis, grid.YAxis.yaxis))
def test_axis(axis):
    g = axis()


# TODO: is there anything to test ?
@pytest.mark.parametrize('axisgrob', (grid.XAxis.xaxisgrob, grid.YAxis.yaxisgrob))
def test_axisgrob(axisgrob):
    g = axisgrob()


# TODO: is there anything to test ?
def test_viewport():
    v = grid.viewport()
