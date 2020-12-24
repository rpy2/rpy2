from rpy2.robjects.packages import (importr,
                                    WeakPackage)
import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    dbplyr = importr('dbplyr', on_conflict="warn")
    dbplyr = WeakPackage(dbplyr._env,
                         dbplyr.__rname__,
                         translation=dbplyr._translation,
                         exported_names=dbplyr._exported_names,
                         on_conflict="warn",
                         version=dbplyr.__version__,
                         symbol_r2python=dbplyr._symbol_r2python,
                         symbol_resolve=dbplyr._symbol_resolve)
TARGET_VERSION = '2.0'
if not dbplyr.__version__.startswith(TARGET_VERSION):
    warnings.warn(
        'This was designed againt dbplyr versions starting with %s'
        ' but you have %s' %
        (TARGET_VERSION, dbplyr.__version__))

sql = dbplyr.sql
