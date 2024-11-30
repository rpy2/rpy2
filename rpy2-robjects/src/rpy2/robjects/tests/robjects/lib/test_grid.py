import pytest
import contextlib
import os
import tempfile

from rpy2.robjects.conversion import localconverter
import rpy2.robjects as robjects
from rpy2.robjects.lib import grid
from rpy2.robjects.vectors import FloatVector, StrVector


@pytest.mark.parametrize(
    'constructor,args,kwargs,res_cls',
    ((grid.unit, (1, 'cm'), {}, grid.Unit),
     (grid.unit, (), {'x': 1, 'units': 'cm'}, grid.Unit),
     (grid.gpar, (), {'col': 'blue'}, grid.Gpar),
     (grid.grob, (), {'name': 'foo'}, grid.Grob),
     (grid.rect, (), {'x': grid.unit(0, 'cm')}, grid.Rect),
     (grid.lines, (), {'x': grid.unit(FloatVector([0, 1]), 'cm')}, grid.Lines),
     (grid.circle, (), {'x': 0}, grid.Circle),
     (grid.points, (), {}, grid.Points),
     (grid.text, ('t0', ), {}, grid.Text),
     (grid.GTree.gtree, (), {}, grid.GTree),
     (grid.GTree.grobtree, (), {}, grid.GTree),
     (grid.XAxis.xaxis, (), {}, grid.XAxis),
     (grid.YAxis.yaxis, (), {}, grid.YAxis),
     (grid.XAxis.xaxisgrob, (), {}, grid.XAxis),
     (grid.YAxis.yaxisgrob, (), {}, grid.YAxis),
    )
)
def test_constructor_and_rpy2py(constructor, args, kwargs, res_cls):
    r_obj = constructor(*args, **kwargs)
    with localconverter(robjects.default_converter + grid.converter) as cv:
        rp_obj = cv.rpy2py(r_obj)
    assert isinstance(rp_obj, res_cls)


# TODO: is there anything to test ?
def test_viewport():
    v = grid.viewport()
