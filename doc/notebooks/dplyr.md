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
mtcars = pandas2ri.ri2py(mtcars)
```
