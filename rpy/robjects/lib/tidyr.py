from collections import namedtuple
from rpy2.robjects.packages import importr, data
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    tidyr = importr('tidyr', on_conflict="warn")
    TARGET_VERSION = '0.3.1'
    if dplyr.__version__ != TARGET_VERSION:
        warnings.warn('This was designed againt tidyr version %s but you have %s' % (TARGET_VERSION, dplyr.__version__))

from rpy2.robjects.lib import dplyr

class DataFrame(dplyr.DataFrame):
    pass

DataFrame.gather = dplyr._wrap(tidyr.gather_, DataFrame)
DataFrame.spread = dplyr._wrap(dplyr.spread_, DataFrame)

gather = dplyr._make_pipe(dplyr.gather_, DataFrame)
spread = dplyr._make_pipe(dplyr.spread_, DataFrame)

