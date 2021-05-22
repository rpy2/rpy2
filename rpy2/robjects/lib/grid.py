"""
Mapping of the R library "grid" for graphics.

The R library provides a low-level coordinate
system and graphic primitives to built visualizations.


"""

import warnings
import rpy2.rinterface as rinterface
import rpy2.robjects as robjects
import rpy2.robjects.conversion as conversion
from rpy2.robjects.packages import importr, WeakPackage

NULL = robjects.NULL

grid = importr('grid')

grid = WeakPackage(grid._env,
                   grid.__rname__,
                   translation=grid._translation,
                   exported_names=grid._exported_names,
                   on_conflict="warn",
                   version=grid.__version__,
                   symbol_r2python=grid._symbol_r2python,
                   symbol_resolve=grid._symbol_resolve)

original_converter = None
converter = conversion.Converter('original grid conversion')
py2rpy = converter.py2rpy
rpy2py = converter.rpy2py

grid_env = robjects.baseenv['as.environment']('package:grid')


layout = grid.grid_layout
newpage = grid.grid_newpage
grill = grid.grid_grill
edit = grid.grid_edit
get = grid.grid_get
remove = grid.grid_remove
add = grid.grid_add
xaxis = grid.grid_xaxis
yaxis = grid.grid_yaxis


class BaseGrid(robjects.RObject):

    @classmethod
    def r(cls, *args, **kwargs):
        """ Constructor (as it looks like on the R side)."""
        res = cls._r_constructor(*args, **kwargs)
        return cls(res)


class Unit(BaseGrid):
    """ Vector of unit values (as in R's grid package) """
    _r_constructor = grid_env['unit']


unit = Unit.r


class Gpar(BaseGrid):
    """ Graphical parameters """
    _r_constructor = grid_env['gpar']
    _get_gpar = grid_env['get.gpar']

    def get(self, names=None):
        return self._get_gpar(names)


gpar = Gpar.r


class Grob(BaseGrid):
    """ Graphical object """
    _r_constructor = grid_env['grob']
    _draw = grid_env['grid.draw']

    def draw(self, recording=True):
        """ Draw a graphical object (calling the R function
        grid::grid.raw())"""
        self._draw(self, recording=recording)


grob = Grob.r


class Rect(Grob):
    _r_constructor = grid_env['rectGrob']


rect = Rect.r


class Lines(Grob):
    _r_constructor = grid_env['linesGrob']


lines = Lines.r


class Circle(Grob):
    _r_constructor = grid_env['circleGrob']


circle = Circle.r


class Points(Grob):
    _r_constructor = grid_env['pointsGrob']


points = Points.r


class Text(Grob):
    _r_constructor = grid_env['textGrob']


text = Text.r


class GTree(Grob):
    """ gTree """
    _gtree = grid_env['gTree']
    _grobtree = grid_env['grobTree']

    @classmethod
    def gtree(cls, **kwargs):
        """ Constructor (uses the R function grid::gTree())"""
        res = cls._gtree(**kwargs)
        return cls(res)

    @classmethod
    def grobtree(cls, **kwargs):
        """ Constructor (uses the R function grid::grobTree())"""
        res = cls._grobtree(**kwargs)
        return cls(res)


class Axis(GTree):
    pass


class XAxis(Axis):
    _xaxis = xaxis
    _xaxisgrob = grid.xaxisGrob

    @classmethod
    def xaxis(cls, **kwargs):
        """ Constructor (uses the R function grid::xaxis())"""
        res = cls._xaxis(**kwargs)
        return cls(res)

    @classmethod
    def xaxisgrob(cls, **kwargs):
        """ Constructor (uses the R function grid::xaxisgrob())"""
        res = cls._xaxisgrob(**kwargs)
        return cls(res)


class YAxis(Axis):
    _yaxis = yaxis
    _yaxisgrob = grid.yaxisGrob

    @classmethod
    def yaxis(cls, **kwargs):
        """ Constructor (uses the R function grid::yaxis())"""
        res = cls._yaxis(**kwargs)
        return cls(res)

    @classmethod
    def yaxisgrob(cls, **kwargs):
        """ Constructor (uses the R function grid::yaxisgrob())"""
        res = cls._yaxisgrob(**kwargs)
        return cls(res)


class Viewport(robjects.RObject):
    """ Drawing context.
    Viewports can be thought of as nodes in a scene graph. """

    _pushviewport = grid_env['pushViewport']
    _popviewport = grid_env['popViewport']
    _current = grid_env['current.viewport']
    _plotviewport = grid_env['plotViewport']
    _downviewport = grid_env['downViewport']
    _seek = grid_env['seekViewport']
    _upviewport = grid_env['upViewport']
    _viewport = grid_env['viewport']

    def push(self, recording=True):
        self._pushviewport(self, recording=recording)

    @classmethod
    def pop(cls, n):
        """ Pop n viewports from the stack. """
        cls._popviewport(n)

    @classmethod
    def current(cls):
        """ Return the current viewport in the stack. """
        cls._current()

    @classmethod
    def default(cls, **kwargs):
        cls._plotviewport(**kwargs)

    @classmethod
    def down(cls, name, strict=False, recording=True):
        """ Return the number of Viewports it went down """
        cls._downviewport(name, strict=strict, recording=recording)

    @classmethod
    def seek(cls, name, recording=True):
        """ Seek and return a Viewport given its name """
        cls._seek(name, recording=recording)

    @classmethod
    def up(cls, n, recording=True):
        """ Go up n viewports """
        cls._downviewport(n, recording=recording)

    @classmethod
    def viewport(cls, **kwargs):
        """ Constructor: create a Viewport """
        res = cls._viewport(**kwargs)
        res = cls(res)
        return res


viewport = Viewport.viewport

_grid_dict = {
    'gpar': Gpar,
    'grob': Grob,
    'gTree': GTree,
    'unit': Unit,
    'xaxis': XAxis,
    'yaxis': YAxis,
    'viewport': Viewport
}

original_py2rpy = None
original_rpy2py = None


# TODO: remove after v3.5.0
def grid_rpy2py(robj):
    warnings.warn('This function is deprecated.',
                  category=DeprecationWarning)
    pyobj = original_rpy2py(robj)

    if not isinstance(pyobj, robjects.RS4):
        rcls = pyobj.rclass
        if rcls is NULL:
            rcls = (None, )
        try:
            cls = _grid_dict[rcls[0]]
            pyobj = cls(pyobj)
        except KeyError:
            pass

    return pyobj


converter._rpy2py_nc_map.update(
    {
        rinterface.FloatSexpVector: conversion.NameClassMap(
            lambda obj: robjects.default_converter.rpy2py(obj),
            {'unit': Unit.r}
        ),
        rinterface.ListSexpVector: conversion.NameClassMap(
            lambda obj: robjects.default_converter.rpy2py(obj),
            {'gpar': Gpar.r,
             'grob': Grob.r}
        ),
    }
)


def activate():
    warnings.warn('The global conversion available with activate() '
                  'is deprecated and will be removed in the next '
                  'major release. Use a local converter.',
                  category=DeprecationWarning)
    global original_converter
    # If module is already activated, there is nothing to do.
    if original_converter is not None:
        return

    original_converter = conversion.converter

    new_converter = conversion.Converter('grid conversion',
                                         template=original_converter)

    for k, v in py2rpy.registry.items():
        if k is object:
            continue
        new_converter.py2rpy.register(k, v)

    for k, v in rpy2py.registry.items():
        if k is object:
            continue
        new_converter.rpy2py.register(k, v)

    conversion.set_conversion(new_converter)


def deactivate():
    global original_converter

    # If module has never been activated or already deactivated,
    # there is nothing to do
    if original_converter is None:
        return

    conversion.set_conversion(original_converter)
    original_converter = None
