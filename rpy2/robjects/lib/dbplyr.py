from rpy2.robjects.packages import (importr,
                                    WeakPackage)
import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    dbplyr = importr('dbplyr', on_conflict="warn")
    dbplyr = WeakPackage(dbplyr)
TARGET_VERSION = '1.4.2'
if dbplyr.__version__ != TARGET_VERSION:
    warnings.warn(
        'This was designed against dbplyr version %s '
        'but you have %s' % (TARGET_VERSION, dbplyr.__version__))

sql = dbplyr.sql
