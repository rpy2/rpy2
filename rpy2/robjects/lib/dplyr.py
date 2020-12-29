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


def _wrap(rfunc, cls):
    def func(dataf, *args, **kwargs):
        res = rfunc(dataf, *args, **kwargs)
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
        res = rfunc(obj, *args, **kwargs)
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

    @property
    def is_grouped_df(self) -> bool:
        """Is the DataFrame in a grouped state"""
        return dplyr.is_grouped_df(self)[0]

    def __rshift__(self, other):
        return other(self)

    @result_as
    def anti_join(self, *args, **kwargs):
        """Call the R function `dplyr::anti_join()`."""
        res = dplyr.anti_join(self, *args, **kwargs)
        return res

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
        return guess_wrap_type(res)(res)

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

    def group_by(self, *args, _add=False,
                 _drop=robjects.rl('group_by_drop_default(.data)')):
        """Call the R function `dplyr::group_by()`."""
        res = dplyr.group_by(self, *args,
                             **{'.add': _add, '.drop': _drop})
        return GroupedDataFrame(res)

    @result_as
    def inner_join(self, *args, **kwargs):
        """Call the R function `dplyr::inner_join()`."""
        res = dplyr.inner_join(self, *args, **kwargs)
        return res

    @result_as
    def left_join(self, *args, **kwargs):
        """Call the R function `dplyr::left_join()`."""
        res = dplyr.left_join(self, *args, **kwargs)
        return res

    @result_as
    def full_join(self, *args, **kwargs):
        """Call the R function `dplyr::full_join()`."""
        res = dplyr.full_join(self, *args, **kwargs)
        return res

    @result_as
    def mutate(self, **kwargs):
        """Call the R function `dplyr::mutate()`."""
        res = dplyr.mutate(self, **kwargs)
        return res

    @result_as
    def mutate_all(self, *args, **kwargs):
        """Call the R function `dplyr::mutate_all()`."""
        res = dplyr.mutate_all(self, *args, **kwargs)
        return res

    @result_as
    def mutate_at(self, *args, **kwargs):
        """Call the R function `dplyr::mutate_at()`."""
        res = dplyr.mutate_at(self, *args, **kwargs)
        return res

    @result_as
    def mutate_if(self, *args, **kwargs):
        """Call the R function `dplyr::mutate_if()`."""
        res = dplyr.mutate_if(self, *args, **kwargs)
        return res

    @result_as
    def right_join(self, *args, **kwargs):
        """Call the R function `dplyr::right_join()`."""
        res = dplyr.right_join(self, *args, **kwargs)
        return res

    @result_as
    def sample_frac(self, *args):
        """Call the R function `dplyr::sample_frac()`."""
        res = dplyr.sample_frac(self, *args)
        return res

    @result_as
    def sample_n(self, *args):
        """Call the R function `dplyr::sample_n()`."""
        res = dplyr.sample_n(self, *args)
        return res

    @result_as
    def select(self, *args):
        """Call the R function `dplyr::select()`."""
        res = dplyr.select(self, *args)
        return res

    @result_as
    def semi_join(self, *args, **kwargs):
        """Call the R function `dplyr::semi_join()`."""
        res = dplyr.semi_join(self, *args, **kwargs)
        return res

    @result_as
    def slice(self, *args, **kwargs):
        """Call the R function `dplyr::slice()`."""
        res = dplyr.slice(self, *args, **kwargs)
        return res

    @result_as
    def slice_head(self, *args, **kwargs):
        """Call the R function `dplyr::slice_head()`."""
        res = dplyr.slice_head(self, *args, **kwargs)
        return res

    @result_as
    def slice_min(self, *args, **kwargs):
        """Call the R function `dplyr::slice_min()`."""
        res = dplyr.slice_min(self, *args, **kwargs)
        return res

    @result_as
    def slice_max(self, *args, **kwargs):
        """Call the R function `dplyr::slice_max()`."""
        res = dplyr.slice_max(self, *args, **kwargs)
        return res

    @result_as
    def slice_sample(self, *args, **kwargs):
        """Call the R function `dplyr::slice_sample()`."""
        res = dplyr.slice_sample(self, *args, **kwargs)
        return res

    @result_as
    def slice_tail(self, *args, **kwargs):
        """Call the R function `dplyr::slice_tail()`."""
        res = dplyr.slice_tail(self, *args, **kwargs)
        return res

    def summarize(self, *args, **kwargs):
        """Call the R function `dplyr::summarize()`.

        This can return a GroupedDataFrame or a DataFrame.
        """
        res = dplyr.summarize(self, *args, **kwargs)
        return guess_wrap_type(res)(res)

    summarise = summarize

    def summarize_all(self, *args, **kwargs):
        """Call the R function `dplyr::summarize_all()`.

        This can return a GroupedDataFrame or a DataFrame.
        """
        res = dplyr.summarize_all(self, *args, **kwargs)
        return guess_wrap_type(res)(res)

    summarise_all = summarize_all

    def summarize_at(self, *args, **kwargs):
        """Call the R function `dplyr::summarize_at()`.

        This can return a GroupedDataFrame or a DataFrame.
        """
        res = dplyr.summarize_at(self, *args, **kwargs)
        return guess_wrap_type(res)(res)

    summarise_at = summarize_at

    def summarize_if(self, *args, **kwargs):
        """Call the R function `dplyr::summarize_if()`.

        This can return a GroupedDataFrame or a DataFrame.
        """
        res = dplyr.summarize_if(self, *args, **kwargs)
        return guess_wrap_type(res)(res)

    summarise_if = summarize_if

    @result_as
    def tally(self, *args, **kwargs):
        """Call the R function `dplyr::transmute()`."""
        res = dplyr.tally(self, *args, **kwargs)
        return res

    @result_as
    def transmute(self, *args, **kwargs):
        """Call the R function `dplyr::transmute()`."""
        res = dplyr.transmute(self, *args, **kwargs)
        return res

    @result_as
    def transmute_all(self, *args, **kwargs):
        """Call the R function `dplyr::transmute_all()`."""
        res = dplyr.transmute_all(self, *args, **kwargs)
        return res

    @result_as
    def transmute_at(self, *args, **kwargs):
        """Call the R function `dplyr::transmute_at()`."""
        res = dplyr.transmute_at(self, *args, **kwargs)
        return res

    @result_as
    def transmute_if(self, *args, **kwargs):
        """Call the R function `dplyr::transmute_if()`."""
        res = dplyr.transmute_if(self, *args, **kwargs)
        return res


def guess_wrap_type(x):
    if dplyr.is_grouped_df(x)[0]:
        return GroupedDataFrame
    else:
        return DataFrame


class GroupedDataFrame(DataFrame):
    """DataFrame grouped by one of several factors."""

    def ungroup(self, *args):
        res = dplyr.ungroup(self, *args)
        return guess_wrap_type(res)(res)


DataFrame.union = _wrap2(dplyr.union_data_frame, None)
DataFrame.intersect = _wrap2(dplyr.intersect_data_frame, None)
DataFrame.setdiff = _wrap2(dplyr.setdiff_data_frame, None)

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
union = _make_pipe2(dplyr.union_data_frame, DataFrame)
intersect = _make_pipe2(dplyr.intersect_data_frame, DataFrame)
setdiff = _make_pipe2(dplyr.setdiff_data_frame, DataFrame)
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
