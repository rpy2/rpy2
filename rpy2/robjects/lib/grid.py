"""
Mapping of the R library "grid" for graphics.

The R library provides a low-level coordinate
system and graphic primitives to built visualizations.


"""

import rpy2.robjects as robjects
import rpy2.robjects.conversion as conversion
from rpy2.rlike.container import OrdDict
from rpy2.robjects.packages import importr, WeakPackage

NULL = robjects.NULL

grid = importr('grid')

grid = WeakPackage(grid)

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


class Unit(robjects.RObject):
    """ Vector of unit values (as in R's grid package) """
    _unit = grid_env['unit']

    @classmethod
    def unit(cls, *args, **kwargs):
        """ Constructor (uses the R function grid::unit())"""
        res = cls._unit(*args, **kwargs)
        return res


unit = Unit.unit


class Gpar(robjects.RObject):
    """ Graphical parameters """
    _gpar = grid_env['gpar']
    _get_gpar = grid_env['get.gpar']

    @classmethod
    def gpar(cls, *args, **kwargs):
        """ Constructor (uses the R function grid::gpar())"""
        res = cls._gpar(*args, **kwargs)
        return res

    def get(self, names=None):
        return self._get_gpar(names)


gpar = Gpar.gpar


class Grob(robjects.RObject):
    """ Graphical object """
    _grob = grid_env['grob']
    _draw = grid_env['grid.draw']

    def __init__(self, *args, **kwargs):
        od = OrdDict()
        for item in args:
            od[None] = conversion.py2rpy(item)
        for k, v in kwargs.items():
            od[k] = conversion.py2rpy(v)
        res = self._constructor.rcall(tuple(od.items()), robjects.globalenv)
        super().__init__(res.__sexp__)

    @classmethod
    def grob(cls, **kwargs):
        """ Constructor (uses the R function grid::grob())"""
        res = cls._grob(**kwargs)
        return res

    def draw(self, recording=True):
        """ Draw a graphical object (calling the R function
        grid::grid.raw())"""
        self._draw(self, recording=recording)


grob = Grob.grob


class Rect(Grob):
    _constructor = grid_env['rectGrob']


rect = Rect


class Lines(Grob):
    _constructor = grid_env['linesGrob']


lines = Lines


class Circle(Grob):
    _constructor = grid_env['circleGrob']


circle = Circle


class Points(Grob):
    _constructor = grid_env['pointsGrob']


points = Points


class Text(Grob):
    _constructor = grid_env['textGrob']


text = Text


class GTree(Grob):
    """ gTree """
    _gtree = grid_env['gTree']
    _grobtree = grid_env['grobTree']

    @classmethod
    def gtree(cls, **kwargs):
        """ Constructor (uses the R function grid::gTree())"""
        res = cls._gtree(**kwargs)
        return res

    @classmethod
    def grobtree(cls, **kwargs):
        """ Constructor (uses the R function grid::grobTree())"""
        res = cls._grobtree(**kwargs)
        return res


class Axis(GTree):
    pass


class XAxis(Axis):
    _xaxis = xaxis
    _xaxisgrob = grid.xaxisGrob

    @classmethod
    def xaxis(cls, **kwargs):
        """ Constructor (uses the R function grid::xaxis())"""
        res = cls._xaxis(**kwargs)
        return res

    @classmethod
    def xaxisgrob(cls, **kwargs):
        """ Constructor (uses the R function grid::xaxisgrob())"""
        res = cls._xaxisgrob(**kwargs)
        return res


class YAxis(Axis):
    _yaxis = yaxis
    _yaxisgrob = grid.yaxisGrob

    @classmethod
    def yaxis(cls, **kwargs):
        """ Constructor (uses the R function grid::yaxis())"""
        res = cls._yaxis(**kwargs)
        return res

    @classmethod
    def yaxisgrob(cls, **kwargs):
        """ Constructor (uses the R function grid::yaxisgrob())"""
        res = cls._yaxisgrob(**kwargs)
        return res


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


def grid_rpy2py(robj):

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


def activate():
    global original_py2rpy, original_rpy2py

    # If module is already activated, there is nothing to do
    if original_py2rpy:
        return

    original_py2rpy = conversion.py2rpy
    original_rpy2py = conversion.rpy2py

    conversion.rpy2py = grid_rpy2py


def deactivate():
    global original_py2rpy, original_rpy2py

    # If module has never been activated or already deactivated,
    # there is nothing to do
    if not original_py2rpy:
        return

    conversion.py2rpy = original_py2rpy
    conversion.rpy2py = original_rpy2py
    original_py2rpy = original_rpy2py = None
