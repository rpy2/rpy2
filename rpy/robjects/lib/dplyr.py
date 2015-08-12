from rpy2.robjects.packages import importr, data
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    dplyr = importr('dplyr', on_conflict="warn")
from rpy2 import robjects

def _wrap(rfunc, cls):
    """ Create a wrapper for `rfunc` that wrap its result in a call
    to the constructor of class `cls` """
    def func(*args, **kwargs):
    	return cls(rfunc(*args, **kwargs))
    return func

def _make_pipe(rfunc, cls):
    def func(*args, **kwargs):
        def func2(obj):
            return cls(rfunc(obj, *args, **kwargs))
        return func2
    return func

class DataFrame(robjects.DataFrame):
    def __rshift__(self, other):
        return other(self)

class GroupedDataFrame(robjects.DataFrame):
    pass

DataFrame.mutate = _wrap(dplyr.mutate_, DataFrame)
DataFrame.filter = _wrap(dplyr.filter_, DataFrame)
DataFrame.select = _wrap(dplyr.select_, DataFrame)
DataFrame.group_by = _wrap(dplyr.group_by_, GroupedDataFrame)
DataFrame.distinct = _wrap(dplyr.distinct_, DataFrame)
DataFrame.inner_join = _wrap(dplyr.inner_join, DataFrame)

GroupedDataFrame.summarize = _wrap(dplyr.summarize_, DataFrame)

mutate = _make_pipe(dplyr.mutate_, DataFrame)
filter = _make_pipe(dplyr.filter_, DataFrame)
select = _make_pipe(dplyr.select_, DataFrame)
group_by = _make_pipe(dplyr.group_by_, DataFrame)
summarize = _make_pipe(dplyr.summarize_, DataFrame)
distinct = _make_pipe(dplyr.distinct_, DataFrame)
inner_join = _make_pipe(dplyr.inner_join, DataFrame)

