from collections import namedtuple
from rpy2 import robjects
from rpy2.robjects.packages import (importr,
                                    WeakPackage)
import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    dplyr_ = importr('dplyr', on_conflict="warn")
    lazyeval = importr('lazyeval', on_conflict="warn")
    rlang = importr('rlang', on_conflict='warn',
                    robject_translations={'.env': '__env'})
    dplyr = WeakPackage(dplyr_._env,
                        dplyr_.__rname__,
                        translation=dplyr_._translation,
                        exported_names=dplyr_._exported_names,
                        on_conflict="warn",
                        version=dplyr_.__version__,
                        symbol_r2python=dplyr_._symbol_r2python,
                        symbol_resolve=dplyr_._symbol_resolve)

TARGET_VERSION = '1.0'
if not dplyr.__version__.startswith(TARGET_VERSION):
    warnings.warn(
        'This was designed againt dplyr versions starting with %s'
        ' but you have %s' %
        (TARGET_VERSION, dplyr.__version__))

StringInEnv = namedtuple('StringInEnv', 'string env')


def _fix_args_inenv(args, env):
    """Use R's lazyeval::as_lazy to evaluate each argument in a sequence as
    code in an environment."""
    args_inenv = list()
    for v in args:
        if isinstance(v, StringInEnv):
            args_inenv.append(lazyeval.as_lazy(v.string, env=v.env))
        else:
            args_inenv.append(lazyeval.as_lazy(v, env=env))
    return args_inenv


def _fix_kwargs_inenv(kwargs, env):
    """Use R's lazyeval::as_lazy to evaluate each value in a dict as
    code in an environment."""
    kwargs_inenv = dict()
    for k, v in kwargs.items():
        if isinstance(v, StringInEnv):
            kwargs_inenv[k] = lazyeval.as_lazy(v.string, env=v.env)
        else:
            kwargs_inenv[k] = lazyeval.as_lazy(v, env=env)
    return kwargs_inenv

# TODO: _wrap and _pipe have become quite similar (identical ?).
#       Have only one of the two ?


def _wrap(rfunc, cls, env=robjects.globalenv):
    def func(dataf, *args, **kwargs):
        args_inenv = _fix_args_inenv(args, env)
        kwargs_inenv = _fix_kwargs_inenv(kwargs, env)
        res = rfunc(dataf, *args_inenv, **kwargs_inenv)
        if cls is None:
            return type(dataf)(res)
        else:
            return cls(res)
    return func


def _wrap2(rfunc, cls, env=robjects.globalenv):
    def func(dataf_a, dataf_b, *args, **kwargs):
        res = rfunc(dataf_a, dataf_b,
                    *args, **kwargs)
        if cls is None:
            return type(dataf_a)(res)
        else:
            return cls(res)
    return func


def _make_pipe(rfunc, cls, env=robjects.globalenv):
    """
    :param rfunc: An R function.
    :param cls: The class to use wrap the result of `rfunc`.
    :param env: A R environment.
    :rtype: A function."""
    def inner(obj, *args, **kwargs):
        args_inenv = _fix_args_inenv(args, env)
        kwargs_inenv = _fix_kwargs_inenv(kwargs, env)
        res = rfunc(obj, *args_inenv, **kwargs_inenv)
        return cls(res)
    return inner


def _make_pipe2(rfunc, cls, env=robjects.globalenv):
    """
    :param rfunc: An R function.
    :param cls: The class to use wrap the result of `rfunc`.
    :param env: A R environment.
    :rtype: A function."""
    def inner(obj_a, obj_b, *args, **kwargs):
        res = rfunc(obj_a, obj_b, *args, **kwargs)
        return cls(res)
    return inner


def _fix_call(func):
    def inner(self, *args, **kwargs):
        if len(args) > 0:
            if len(kwargs) > 0:
                res = func(self, *args, **kwargs)
            else:
                res = func(self, *args)
        else:
            if len(kwargs) > 0:
                res = func(self, **kwargs)
            else:
                res = func(self)
        return res
    return inner


def result_as(func, constructor=None):
    """Wrap the result using the constructor.

    This decorator is intended for methods. The first arguments
    passed to func must be 'self'.

    Args:
    constructor: a constructor to call using the result of func(). If None,
    the type of self will be used."""
    def inner(self, *args, **kwargs):
        if constructor is None:
            wrap = type(self)
        else:
            wrap = constructor
        res = func(self, *args, **kwargs)
        return wrap(res)
    return inner


class DataFrame(robjects.DataFrame):
    """DataFrame object extending the object of the same name in
    `rpy2.robjects.vectors` with functionalities defined in the R
    package `dplyr`."""

    def __rshift__(self, other):
        return other(self)

    @result_as
    def arrange(self, *args, _by_group=False):
        """Call the R function `dplyr::arrange()`."""
        res = dplyr.arrange(self, *args, **{'.by_group': _by_group})
        return res

    def copy_to(self, destination, name, **kwargs):
        """
        - destination: database
        - name: table name in the destination database
        """
        res = dplyr.copy_to(destination, self, name=name)
        return res

    @result_as
    def collapse(self, *args, **kwargs):
        """
        Call the function `collapse` in the R package `dplyr`.
        """
        return dplyr.collapse(self, *args, **kwargs)

    @result_as
    def collect(self, *args, **kwargs):
        """Call the function `collect` in the R package `dplyr`."""
        return dplyr.collect(self, *args, **kwargs)

    @result_as
    def count(self, *args, **kwargs):
        """Call the function `count` in the R package `dplyr`."""
        return dplyr.count(self, *args, **kwargs)

    @result_as
    def distinct(self, *args, _keep_all=False):
        """Call the R function `dplyr::distinct()`."""
        res = dplyr.distinct(self, *args, **{'.keep_all': _keep_all})
        return res

    @result_as
    def filter(self, *args, _preserve=False):
        """Call the R function `dplyr::filter()`."""
        res = dplyr.filter(self, *args, **{'.preserve': _preserve})
        return res

    def group_by(self, *args):
        """Call the R function `dplyr::group_by()`."""
        res = dplyr.group_by(self, *args)
        return GroupedDataFrame(res)

    @result_as
    def mutate(self, **kwargs):
        """Call the R function `dplyr::mutate()`."""
        res = dplyr.mutate(self, **kwargs)
        return res

    @result_as
    def select(self, *args):
        """Call the R function `dplyr::select()`."""
        res = dplyr.select(self, *args)
        return res

    @result_as
    def transmute(self, *args, **kwargs):
        """Call the R function `dplyr::transmute()`."""
        res = dplyr.transmute(self, *args, **kwargs)
        return res


def guess_wrap_type(x):
    if dplyr.is_grouped_df(x):
        return GroupedDataFrame
    else:
        return DataFrame


class GroupedDataFrame(DataFrame):
    """DataFrame grouped by one of several factors."""

    def summarize(self, *args, **kwargs):
        """Call the R function `dplyr::summarize()`.

        This can return a GroupedDataFrame or a DataFrame.
        """
        res = dplyr.summarize(self, *args, **kwargs)
        return guess_wrap_type(res)(res)

    def ungroup(self, *args,
                _add=False, _drop=robjects.rl('group_by_drop_default(.data)')):
        res = dplyr.ungroup(*args, _add=_add, _drop=_drop)
        return guess_wrap_type(res)(res)

    summarise = summarize


DataFrame.inner_join = _wrap2(dplyr.inner_join, None)
DataFrame.left_join = _wrap2(dplyr.left_join, None)
DataFrame.right_join = _wrap2(dplyr.right_join, None)
DataFrame.full_join = _wrap2(dplyr.full_join, None)
DataFrame.semi_join = _wrap2(dplyr.semi_join, None)
DataFrame.anti_join = _wrap2(dplyr.anti_join, None)
DataFrame.union = _wrap2(dplyr.union, None)
DataFrame.intersect = _wrap2(dplyr.intersect, None)
DataFrame.setdiff = _wrap2(dplyr.setdiff, None)

DataFrame.sample_n = _wrap(dplyr.sample_n, None)
DataFrame.sample_frac = _wrap(dplyr.sample_frac, None)
DataFrame.slice = _wrap(dplyr.slice_, None)
DataFrame.tally = _wrap(dplyr.tally, None)

DataFrame.mutate_if = _wrap(dplyr.mutate_if, None)
DataFrame.mutate_at = _wrap(dplyr.mutate_at, None)
DataFrame.mutate_all = _wrap(dplyr.mutate_all, None)
DataFrame.summarize_all = _wrap(dplyr.summarize_all, None)
DataFrame.summarise_all = _wrap(dplyr.summarize_all, None)
DataFrame.summarize_at = _wrap(dplyr.summarize_at, None)
DataFrame.summarise_at = _wrap(dplyr.summarize_at, None)
DataFrame.summarize_if = _wrap(dplyr.summarize_if, None)
DataFrame.summarise_if = _wrap(dplyr.summarize_if, None)
DataFrame.transmute_all = _wrap(dplyr.transmute_all, None)
DataFrame.transmute_if = _wrap(dplyr.transmute_if, None)
DataFrame.transmute_at = _wrap(dplyr.transmute_at, None)

arrange = _make_pipe(dplyr.arrange, DataFrame)
count = _make_pipe(dplyr.count, DataFrame)
mutate = _make_pipe(dplyr.mutate, DataFrame)
transmute = _make_pipe(dplyr.transmute, DataFrame)
filter = result_as(dplyr.filter)
select = _make_pipe(dplyr.select, DataFrame)
group_by = _make_pipe(dplyr.group_by, GroupedDataFrame)
summarize = _make_pipe(dplyr.summarize, guess_wrap_type)
summarise = summarize
distinct = _make_pipe(dplyr.distinct, DataFrame)
inner_join = _make_pipe2(dplyr.inner_join, DataFrame)
left_join = _make_pipe2(dplyr.left_join, DataFrame)
right_join = _make_pipe2(dplyr.right_join, DataFrame)
full_join = _make_pipe2(dplyr.full_join, DataFrame)
semi_join = _make_pipe2(dplyr.semi_join, DataFrame)
anti_join = _make_pipe2(dplyr.anti_join, DataFrame)
union = _make_pipe2(dplyr.union, DataFrame)
intersect = _make_pipe2(dplyr.intersect, DataFrame)
setdiff = _make_pipe2(dplyr.setdiff, DataFrame)
sample_n = _make_pipe(dplyr.sample_n, DataFrame)
sample_frac = _make_pipe(dplyr.sample_frac, DataFrame)
slice = _make_pipe(dplyr.slice_, DataFrame)
tally = _make_pipe(dplyr.tally, DataFrame)

mutate_if = _make_pipe(dplyr.mutate_if, DataFrame)
mutate_at = _make_pipe(dplyr.mutate_at, DataFrame)
mutate_all = _make_pipe(dplyr.mutate_all, DataFrame)
summarize_all = _make_pipe(dplyr.summarize_all, DataFrame)
summarise_all = _make_pipe(dplyr.summarise_all, DataFrame)
summarize_at = _make_pipe(dplyr.summarize_at, DataFrame)
summarise_at = _make_pipe(dplyr.summarize_at, DataFrame)
summarize_if = _make_pipe(dplyr.summarize_if, DataFrame)
summarise_if = _make_pipe(dplyr.summarize_if, DataFrame)
transmute_all = _make_pipe(dplyr.transmute_all, DataFrame)
transmute_if = _make_pipe(dplyr.transmute_if, DataFrame)
transmute_at = _make_pipe(dplyr.transmute_at, DataFrame)


# Functions for databases
class DataSource(robjects.ListVector):
    """ Source of data tables (e.g., in a schema in a relational database). """

    @property
    def tablenames(self):
        """ Call the R function dplyr::src_tbls() and return a vector
        of table names."""
        return tuple(dplyr.src_tbls(self))

    def get_table(self, name):
        """ "Get" table from a source (R dplyr's function `tbl`). """
        return DataFrame(tbl(self, name))


src = dplyr.src
src_tbls = dplyr.src_tbls

src_local = dplyr.src_local
src_df = dplyr.src_df


def src_mysql(*args, **kwargs):
    res = dplyr.src_mysql(*args, **kwargs)
    return DataSource(res)


def src_postgres(*args, **kwargs):
    res = dplyr.src_postgres(*args, **kwargs)
    return DataSource(res)


def src_sqlite(*args, **kwargs):
    res = dplyr.src_sqlite(*args, **kwargs)
    return DataSource(res)


def copy_to(*args, **kwargs):
    res = dplyr.copy_to(*args, **kwargs)
    return DataFrame(res)


# Generic to create a data table
tbl = dplyr.tbl


# TODO: wrapper classes for the output of the following two function.
explain = dplyr.explain
show_query = dplyr.show_query
