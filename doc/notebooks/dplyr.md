# dplyr in Python

We need 2 things for this:

1- A data frame (using one of R's demo datasets).

```python
from rpy2.robjects.packages import importr, data
datasets = importr('datasets')
mtcars_env = data(datasets).fetch('mtcars')
mtcars = mtcars_env['mtcars']
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

print(dataf)
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

print(dataf)
```

And if the starting point is a pandas data frame,
do the following and start over again.

```python 
from rpy2.robjects import pandas2ri
pandas2ri.activate()
mtcars = pandas2ri.ri2py(mtcars)
```

Thrilling, isn't it ?

The strings passed to the dplyr function are evaluated as expression,
just like this is happening when using dplyr in R. This means that
when writing `'mean(powertoweight)'` the R function `mean()` is used.

Using an Python function is not too difficult though. We can just
call Python back from R:

```python
from rpy2.rinterface import rternalize
@rternalize
def mean_np(x):
    import numpy
    return numpy.mean(x)

from rpy2.robjects import globalenv
globalenv['mean_np'] = mean_np

dataf = (DataFrame(mtcars) >>
         filter('gear>3') >>
         mutate(powertoweight='hp*36/wt') >>
         group_by('gear') >>
         summarize(mean_ptw='mean(powertoweight)',
	           mean_np_ptw='mean_np(powertoweight)'))

print(dataf)
```

**note**: This will only work when the issue 1323 in dplyr is fixed
(https://github.com/hadley/dplyr/issues/1323)
