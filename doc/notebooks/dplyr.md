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
```

With this we have the choice of chaining (D3-style)

```python
dataf = (DataFrame(mtcars).
         filter('gear>3').
         mutate(powertoweight='hp*36/wt').
         group_by('gear').
         summarize(mean_ptw='mean(powertoweight)'))

dataf
```

or piping (magrittr style).


```python
from rpy2.robjects.lib.dplyr import (filter,
                                     mutate,
                                     group_by,
                                     summarize)

dataf = (DataFrame(mtcars) >>
         filter('gear>3') >>
         mutate(powertoweight='hp*36/wt') >>
         group_by('gear') >>
         summarize(mean_ptw='mean(powertoweight)'))

dataf
```

The strings passed to the dplyr function are evaluated as expression,
just like this is happening when using dplyr in R. This means that
when writing `mean(powertoweight)` the R function `mean()` is used.

Using a Python function is not too difficult though. We can just
call Python back from R. To achieve this we simply
use the decorator `rternalize`.

```python
# Define a python function, and make
# it a function R can use through `rternalize`
from rpy2.rinterface import rternalize
@rternalize
def mean_np(x):
    import numpy
    return numpy.mean(x)

# Bind that function to a symbol in R's
# global environment
from rpy2.robjects import globalenv
globalenv['mean_np'] = mean_np

# Write a dplyr chain of operations,
# using our Python function `mean_np`
dataf = (DataFrame(mtcars) >>
         filter('gear>3') >>
         mutate(powertoweight='hp*36/wt') >>
         group_by('gear') >>
         summarize(mean_ptw='mean(powertoweight)',
                   mean_np_ptw='mean_np(powertoweight)'))

dataf
```

It is also possible to carry this out without having to
place the custom function in R's global environment.

```python
del(globalenv['mean_np'])
```

```python
from rpy2.robjects.lib.dplyr import StringInEnv
from rpy2.robjects import Environment
my_env = Environment()
my_env['mean_np'] = mean_np

dataf = (DataFrame(mtcars) >>
         filter('gear>3') >>
         mutate(powertoweight='hp*36/wt') >>
         group_by('gear') >>
         summarize(mean_ptw='mean(powertoweight)',
                   mean_np_ptw=StringInEnv('mean_np(powertoweight)',
                                           my_env)))

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
    res = (dataf_db >>
           filter('gear>3') >>
           mutate(powertoweight='hp*36/wt') >>
           group_by('gear') >>
           summarize(mean_ptw='mean(powertoweight)'))
    print(res)
# 
```

Since we are manipulating R objects, anything available to R is also available
to us. If we want to see the SQL code generated that's:

```python
print(res.rx2("query")["sql"])
```

And if the starting point is a pandas data frame,
do the following and start over again.

```python 
from rpy2.robjects import pandas2ri
from rpy2.robjects import default_converter
from rpy2.robjects.conversion import localconverter
with localconverter(default_converter + pandas2ri.converter) as cv:
    mtcars = mtcars_env['mtcars']
    mtcars = pandas2ri.ri2py(mtcars)
print(type(mtcars))
```

Using a local converter lets us also go from the pandas data frame to our dplyr-augmented R data frame.

```python
with localconverter(default_converter + pandas2ri.converter) as cv:
    dataf = (DataFrame(mtcars).
             filter('gear>=3').
             mutate(powertoweight='hp*36/wt').
             group_by('gear').
             summarize(mean_ptw='mean(powertoweight)'))

dataf
```

**Reuse. Get things done. Don't reimplement.**
