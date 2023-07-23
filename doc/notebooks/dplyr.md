# dplyr in Python

We need 2 things for this:

1- A data frame (using one of R's demo datasets).

```python
from rpy2.robjects.packages import importr, data
datasets = importr('datasets')
mtcars_env = data(datasets).fetch('mtcars')
mtcars = mtcars_env['mtcars']
```

In addition to that, and because this tutorial is in a notebook,
we initialize HTML rendering for R objects (pretty display of
R data frames).

```python
import rpy2.ipython.html
rpy2.ipython.html.init_printing()
```

2- dplyr

```python
from rpy2.robjects.lib.dplyr import DataFrame
from rpy2.robjects import rl
```

With this we have the choice of chaining (D3-style)

```python
dataf = (
    DataFrame(mtcars)
    .filter(rl('gear>3'))
    .mutate(powertoweight=rl('hp*36/wt'))
    .group_by(rl('gear'))
    .summarize(mean_ptw=rl('mean(powertoweight)'))
)

dataf
```

or with pipes (magrittr style).


```python
# currently no longer working
from rpy2.robjects.lib.dplyr import (filter,
                                     mutate,
                                     group_by,
                                     summarize)

if False:
    dataf = (DataFrame(mtcars) >>
             filter(rl('gear>3')) >>
             mutate(powertoweight=rl('hp*36/wt')) >>
             group_by(rl('gear')) >>
             summarize(mean_ptw=rl('mean(powertoweight)')))

    dataf
```

The function `rl` creates unevaluated R language objects, which
are then consummed by the `dplyr` function, just like it would be
happening when using `dplyr` in R itself. This means that
when writing `mean(powertoweight)` the R function `mean()` is used.

Using a Python function is not too difficult though. We can just
call Python back from R. To achieve this we simply
use the decorator `rternalize`.

```python
# Define a python function, and make
# it a function R can use through `rternalize`
from rpy2.rinterface import rternalize
@rternalize(signature=False)
def mean_np(x):
    import statistics
    return statistics.mean(x)

# Bind that function to a symbol in R's
# global environment
from rpy2.robjects import globalenv
globalenv['mean_np'] = mean_np

# Write a dplyr chain of operations,
# using our Python function `mean_np`
dataf = (
    DataFrame(mtcars)
    .filter(rl('gear>3'))
    .mutate(powertoweight=rl('hp*36/wt'))
    .group_by(rl('gear'))
    .summarize(mean_ptw=rl('mean(powertoweight)'),
               mean_np_ptw=rl('mean_np(powertoweight)'))
)

dataf
```

It is also possible to carry this out without having to
place the custom function in R's global environment, although
this is not straightforward.

```python
# First we delete our Python callback in globalenv to
# ensure that we are picking up our callback in our
# specific environment rather than this one.
del(globalenv['mean_np'])

from rpy2.robjects import Environment
my_env = Environment()
my_env['mean_np'] = mean_np


# Create an rlang "quosure" object within
# a given environment. We use the R package
# rlang used by dplyr.
from rpy2.robjects.lib.dplyr import rlang

myquo = rlang.quo.rcall(
    [(None, rl('mean_np(rlang::enexpr(powertoweight))'))],
    environment=my_env
)

dataf = (
    DataFrame(mtcars)
    .filter(rl('gear>3'))
    .mutate(powertoweight=rl('hp*36/wt'))
    .group_by(rl('gear'))
    .summarize(
        mean_ptw=rl('mean(powertoweight)'),
        mean_np_ptw=myquo)
)

dataf
```


**note**: rpy2's interface to dplyr is implementing a fix to the (non-?)issue 1323
(https://github.com/hadley/dplyr/issues/1323)

The seamless translation of transformations to SQL whenever the
data are in a table can be used directly. Since we are lifting
the original implementation of `dplyr`, it *just works*.

```python
from rpy2.robjects.lib.dplyr import dplyr
# in-memory SQLite database broken in dplyr's src_sqlite
# db = dplyr.src_sqlite(":memory:")
import tempfile
with tempfile.NamedTemporaryFile() as db_fh:
    db = dplyr.src_sqlite(db_fh.name)
    # copy the table to that database
    dataf_db = DataFrame(mtcars).copy_to(db, name="mtcars")
    res = (dataf_db
           .filter(rl('gear>3'))
           .mutate(powertoweight=rl('hp*36/wt'))
           .group_by(rl('gear'))
           .summarize(mean_ptw=rl('mean(powertoweight)')))
    print(res)
# 
```

Since we are manipulating R objects, anything available to R is also available
to us. If we want to see the SQL code generated that's:

```python
silent = dplyr.show_query(res)
```

The conversion rules in rpy2 make the above easily applicable to pandas data frames,
completing the "lexical loan" of the dplyr vocabulary from R.


```python 
from rpy2.robjects import pandas2ri
from rpy2.robjects import default_converter

# Using a conversion context in which the pandas conversion is
# added to the default conversion rules, the rpy2 object
# `mtcars` (an R data frame) is converted to a pandas data frame.
with (default_converter + pandas2ri.converter).context() as cv:
    pd_mtcars = mtcars_env['mtcars']
print(type(pd_mtcars))
```

Using a local conversion context lets us also go from the pandas data frame
to our dplyr-augmented R data frame and use the dplyr transformations
on it.

```python
with (default_converter + pandas2ri.converter).context() as cv:
    dataf = (DataFrame(pd_mtcars)
             .filter(rl('gear>=3'))
             .mutate(powertoweight=rl('hp*36/wt'))
             .group_by(rl('gear'))
             .summarize(mean_ptw=rl('mean(powertoweight)')))

dataf
```

**Reuse. Get things done. Don't reimplement.**
