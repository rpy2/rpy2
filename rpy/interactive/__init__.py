"""
Package to interface with R, with a focus on interactive usage
(REPL approach to code-writing), although the package will work
in non-interactive settings.

The package aims at being simple rather than exhaustively complete
(rpy2.robjects, or rpy2.rinterface, can be used if needed), providing
a comfortable experience with autocompletion-capable python consoles.
"""



from rpy2.robjects.packages import importr as _importr
from rpy2.robjects.vectors import IntVector, FloatVector, ComplexVector
from rpy2.robjects.vectors import Array, Matrix
from rpy2.robjects.vectors import StrVector
from rpy2.robjects.vectors import ListVector, DataFrame
from rpy2.robjects.environments import Environment
from rpy2.robjects import Formula
import process_revents as revents

class Packages(object):
    __instance = None
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def __setattr__(self, name, value):
        raise AttributeError("Attributes cannot be set. Use 'importr'")

def importr(packname, newname=None):

    assert isinstance(packname, str)
    packinstance = _importr(packname)

    if newname is None:
        newname = packname.replace('.', '_')

    Packages().__dict__[newname] = packinstance
    return packinstance

importr('base')

packages = Packages()

revents.start()

