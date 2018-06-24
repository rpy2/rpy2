from collections import namedtuple
from six import with_metaclass
from rpy2.robjects.packages import (importr, data,
                                    Package, default_symbol_r2python,
                                    default_symbol_check_after,
                                    WeakPackage)
import warnings
    
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    dbplyr = importr('dbplyr', on_conflict="warn")
    lazyeval = importr('lazyeval', on_conflict="warn")
    dbplyr = WeakPackage(dbplyr._env,
                         dbplyr.__rname__,
                         translation=dbplyr._translation,
                         exported_names=dbplyr._exported_names,
                         on_conflict="warn",
                         version=dbplyr.__version__,
                         symbol_r2python=dbplyr._symbol_r2python,
                         symbol_check_after=dbplyr._symbol_check_after)
TARGET_VERSION = '1.2.1'
if dbplyr.__version__ != TARGET_VERSION:
    warnings.warn('This was designed againt dbplyr version %s but you have %s' % (TARGET_VERSION, dbplyr.__version__))

    
from rpy2 import robjects
from rpy2.robjects.lib import dplyr


sql = dbplyr.sql
