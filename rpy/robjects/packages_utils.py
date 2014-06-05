""" Utility module with functions related to R packages
(having these in this utility module rather than in packages.py
prevents circular imports). """

from rpy2 import rinterface

_packages = rinterface.baseenv['.packages']
_libpaths = rinterface.baseenv['.libPaths']
_find_package = rinterface.baseenv['find.package']

def get_packagepath(package):
    """ return the path to an R package installed """
    res = _find_package(rinterface.StrSexpVector((package, )))
    return res[0]


