from collections import namedtuple
from rpy2.robjects.packages import importr, data, WeakPackage
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    tidyr = importr('tidyr', on_conflict="warn")
    
TARGET_VERSION = '0.7.2'
if tidyr.__version__ != TARGET_VERSION:
    warnings.warn('This was designed againt tidyr version %s but you have %s' % (TARGET_VERSION, tidyr.__version__))

tidyr = WeakPackage(tidyr._env,
                    tidyr.__rname__,
                    translation=tidyr._translation,
                    exported_names=tidyr._exported_names,
                    on_conflict="warn",
                    version=tidyr.__version__,
                    symbol_r2python=tidyr._symbol_r2python,
                    symbol_check_after=tidyr._symbol_check_after)


    
from rpy2.robjects.lib import dplyr

class DataFrame(dplyr.DataFrame):
    pass

DataFrame.summarize = dplyr._wrap(dplyr.summarize, DataFrame)
DataFrame.summarise = DataFrame.summarize

def _wrap(rfunc):
    def func(dataf, *args, **kwargs):
        cls = type(dataf)
        res = rfunc(dataf, *args, **kwargs)
        return cls(res)
    return func

DataFrame.gather = _wrap(tidyr.gather_)
DataFrame.spread = _wrap(tidyr.spread_)

