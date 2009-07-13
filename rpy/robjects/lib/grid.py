import rpy2.robjects.methods
import rpy2.robjects as robjects
import rpy2.robjects.conversion as conversion

#getmethod = robjects.baseenv.get("getMethod")

rimport = robjects.baseenv.get('library')
rimport('grid')

grid_env = robjects.baseenv['as.environment']('package:grid')


layout = grid_env['grid.layout']
newpage = grid_env['grid.newpage']


class Grob(robjects.RObject):
    _grob = grid_env['grob']

    @classmethod
    def grob(cls, **kwargs):
        res = cls._grob(**kwargs)
        return res
grob = Grob.grob


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


    rclass = [x for x in pyobj.rclass][0]
    try:
        cls = _grid_dict[rclass]
        pyobj = cls(pyobj)
    except KeyError, ke:
        pass

    return pyobj

conversion.ri2py = grid_conversion
