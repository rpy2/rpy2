# `R` and `pandas` data frames

R `data.frame` and :class:`pandas.DataFrame` objects share a lot of
conceptual similarities, and :mod:`pandas` chose to use the class name
`DataFrame` after R objects.

In a nutshell, both are sequences of vectors (or arrays) of consistent
length or size for the first dimension (the "number of rows").
if coming from the database world, an other way to look at them is
column-oriented data tables, or data table API.

rpy2 is providing an interface between Python and R, and a convenience
conversion layer between :class:`rpy2.robjects.vectors.DataFrame` and
:class:`pandas.DataFrame` objects, implemented in
:mod:`rpy2.robjects.pandas2ri`.

```python
import pandas as pd
import rpy2.robjects as ro
from rpy2.robjects.packages import importr 
from rpy2.robjects import pandas2ri
```

## From `pandas` to `R`

Pandas data frame:

```python
pd_df = pd.DataFrame({'int_values': [1,2,3],
                      'str_values': ['abc', 'def', 'ghi']})

pd_df
```

R data frame converted from a `pandas` data frame:

```python
with (ro.default_converter + pandas2ri.converter).context():
  r_from_pd_df = ro.conversion.get_conversion().py2rpy(pd_df)

r_from_pd_df
```

The conversion is automatically happening when calling R functions.
For example, when calling the R function `base::summary`:

```python
base = importr('base')

with (ro.default_converter + pandas2ri.converter).context():
  df_summary = base.summary(pd_df)
print(df_summary)
```

Note that a `ContextManager` is used to limit the scope of the
conversion. Without it, rpy2 will not know how to convert a pandas
data frame:

```python
try:
  df_summary = base.summary(pd_df)
except NotImplementedError as nie:
  print('NotImplementedError:')
  print(nie)
```

## From `R` to `pandas`

Starting from an R data frame this time:

```python
r_df = ro.DataFrame({'int_values': ro.IntVector([1,2,3]),
                     'str_values': ro.StrVector(['abc', 'def', 'ghi'])})

r_df
```

It can be converted to a pandas data frame using the same converter:

```python
with (ro.default_converter + pandas2ri.converter).context():
  pd_from_r_df = ro.conversion.get_conversion().rpy2py(r_df)

pd_from_r_df
```

## Date and time objects

```python
pd_df = pd.DataFrame({
    'Timestamp': pd.date_range('2017-01-01 00:00:00', periods=10, freq='s')
    })
    
pd_df
```

```python
with (ro.default_converter + pandas2ri.converter).context():
  r_from_pd_df = ro.conversion.py2rpy(pd_df)

r_from_pd_df
```

The timezone used for conversion is the system's default timezone unless
`rpy2.robjects.vectors.default_timezone` is specified...
or unless the time zone is specified in the original time object:

```python
pd_tz_df = pd.DataFrame({
    'Timestamp': pd.date_range('2017-01-01 00:00:00', periods=10, freq='s',
                               tz='UTC')
    })
    
with (ro.default_converter + pandas2ri.converter).context():
  r_from_pd_tz_df = ro.conversion.py2rpy(pd_tz_df)

r_from_pd_tz_df
```
