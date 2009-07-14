import rpy2.robjects.methods
import rpy2.robjects as robjects
import rpy2.robjects.conversion as conversion
from rpy2.rlike.container import OrdDict

#getmethod = robjects.baseenv.get("getMethod")

rimport = robjects.baseenv.get('library')
rimport('grid')

grid_env = robjects.baseenv['as.environment']('package:grid')


layout = grid_env['grid.layout']
newpage = grid_env['grid.newpage']
grill = grid_env['grid.grill']


class Grob(robjects.RObject):
    _grob = grid_env['grob']
    _draw = grid_env['grid.draw']

    def __init__(self, *args, **kwargs):
        od = OrdDict()
        for item in args:
            od[None] = conversion.py2ro(item)
        for k, v in kwargs.iteritems():
            od[k] = conversion.py2ro(v)
        res = self._constructor.rcall(od.items(), robjects.globalenv)
        self.__sexp__ = res.__sexp__

    @classmethod
    def grob(cls, **kwargs):
        res = cls._grob(**kwargs)
        return res

    def draw(self, recording = True):
        self._draw(self, recording = recording)

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

        
class Viewport(robjects.RObject):
    _pushviewport = grid_env['pushViewport']
    _popviewport = grid_env['popViewport']
    _current = grid_env['current.viewport']
    _plotviewport = grid_env['plotViewport']
    _downviewport = grid_env['downViewport']
    _seek = grid_env['seekViewport']
    _upviewport = grid_env['upViewport']
    _viewport = grid_env['viewport']

    def push(self, recording = True):
        self._pushviewport(self, recording = recording)

    @classmethod
    def pop(cls, n):
        cls._popviewport(n)

    @classmethod
    def current(cls):
        cls._current()

    @classmethod
    def default(cls, **kwargs):
        cls._plotviewport(**kwargs)

    @classmethod
    def down(cls, name, strict = False, recording = True):
        cls._downviewport(name, strict = strict, recording = recording)

    @classmethod
    def seek(cls, name, recording = True):
        cls._seek(name, recording = recording)

    @classmethod
    def up(cls, n, recording = True):
        cls._downviewport(n, recording = recording)

    @classmethod
    def viewport(cls, **kwargs):
        res = cls._viewport(**kwargs)
        return res

viewport = Viewport.viewport


_grid_dict = {
    'grob': Grob,
    'viewport': Viewport
}

original_conversion = conversion.ri2py

def grid_conversion(robj):

    pyobj = original_conversion(robj)

    if not isinstance(pyobj, robjects.RS4):
        rclass = tuple(pyobj.rclass)
        try:
            cls = _grid_dict[rclass[0]]
            pyobj = cls(pyobj)
        except KeyError, ke:
            pass

    return pyobj

conversion.ri2py = grid_conversion
