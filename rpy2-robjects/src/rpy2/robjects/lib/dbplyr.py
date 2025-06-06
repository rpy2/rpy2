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
TARGET_VERSION = '2.5.'
if dbplyr.__version__ is None:
    warnings.warn(
        'This was designed against dbplyr versions starting '
        f'with {TARGET_VERSION} but version extraction for '
        'the R package is not working.'
    )
elif not dbplyr.__version__.startswith(TARGET_VERSION):
    warnings.warn(
        'This was designed against dbplyr versions starting '
        f'with {TARGET_VERSION} '
        'but you have {dbplyr.__version__}.'
    )

sql = dbplyr.sql
