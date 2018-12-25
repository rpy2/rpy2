from rpy2.robjects.packages import (importr,
                                    WeakPackage)
from rpy2.robjects.lib import dplyr
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    tidyr = importr('tidyr', on_conflict="warn")

TARGET_VERSION = '0.8.2'

if tidyr.__version__ != TARGET_VERSION:
    warnings.warn('This was designed againt tidyr version %s '
                  'but you have %s' % (TARGET_VERSION, tidyr.__version__))

tidyr = WeakPackage(tidyr._env,
                    tidyr.__rname__,
                    translation=tidyr._translation,
                    exported_names=tidyr._exported_names,
                    on_conflict="warn",
                    version=tidyr.__version__,
                    symbol_r2python=tidyr._symbol_r2python,
                    symbol_check_after=tidyr._symbol_check_after)


def _wrap(rfunc):
    def func(dataf, *args, **kwargs):
        cls = type(dataf)
        res = rfunc(dataf, *args, **kwargs)
        return cls(res)
    return func


class DataFrame(dplyr.DataFrame):
    gather = _wrap(tidyr.gather)
    spread = _wrap(tidyr.spread)


DataFrame.summarize = dplyr._wrap(dplyr.summarize, None)
DataFrame.summarise = DataFrame.summarize
