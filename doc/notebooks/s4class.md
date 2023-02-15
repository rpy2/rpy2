
# Basic handling

The S4 system is one the OOP systems in R.
Its largest use might be in the Bioconductor collection of packages
for bioinformatics and computational biology.

We use the bioconductor `Biobase`:

```python
from rpy2.robjects.packages import importr
biobase = importr('Biobase')
```

The R package contains constructors for the S4 classes defined. They
are simply functions, and can be used as such through `rpy2`:

```python
eset = biobase.ExpressionSet() 
```

The object `eset` is an R object of type `S4`:
```python
type(eset)
```

It has a class as well:

```python
tuple(eset.rclass)
```

In R, objects attributes are also known as slots. The attribute names
can be listed with:

```python
tuple(eset.slotnames())
```

The attributes can also be accessed through the `rpy2` property `slots`.
`slots` is a mapping between attributes names (keys) and their associated
R object (values). It can be used as Python `dict`:

```python
# print keys
print(tuple(eset.slots.keys()))

# fetch `phenoData`
phdat = eset.slots['phenoData']

# phdat is an S4 object itself
pheno_dataf = phdat.slots['data']
```

# Mapping S4 classes to Python classes

Writing one's own Python class extending rpy2's `RS4` is straightforward.
That class can be used wrap our `eset` object

```python

from rpy2.robjects.methods import RS4   
class ExpressionSet(RS4):
    pass

eset_myclass = ExpressionSet(eset)
```

## Custom conversion

The conversion system can also be made aware our new class by customizing
the handling of S4 objects.

A simple implementation is a factory function that will conditionally wrap
the object in our Python class `ExpressionSet`:

```python
def rpy2py_s4(obj):
    if 'ExpressionSet' in obj.rclass:
        res = ExpressionSet(obj)
    else:
        res = robj
    return res

# try it
rpy2py_s4(eset)
```

That function can be be register to a `Converter`:

```python
from rpy2.robjects import default_converter
from rpy2.robjects.conversion import Converter

my_converter = Converter('ExpressionSet-aware converter',
                         template=default_converter)

from rpy2.rinterface import SexpS4
my_converter.rpy2py.register(SexpS4, rpy2py_s4)

```

When using that converter, the matching R objects are returned as
instances of our Python class `ExpressionSet`:

```python

with my_converter.context() as cv:
    eset = biobase.ExpressionSet()
    print(type(eset))
```

## Class attributes

The R attribute `assayData` can be accessed
through the accessor method `exprs()` in R.
We can make it a property in our Python class:

```python
class ExpressionSet(RS4):
    def _exprs_get(self):
        return self.slots['assayData']
    def _exprs_set(self, value):
        self.slots['assayData'] = value
    exprs = property(_exprs_get,
                     _exprs_set,
                     None,
                     "R attribute `exprs`")
eset_myclass = ExpressionSet(eset)

eset_myclass.exprs
```

## Methods

In R's S4 methods are generic functions served by a multiple dispatch system.

A natural way to expose the S4 method to Python is to use the
`multipledispatch` package:

```python
from multipledispatch import dispatch
from functools import partial

my_namespace = dict()
dispatch = partial(dispatch, namespace=my_namespace)

@dispatch(ExpressionSet)
def rowmedians(eset,
               na_rm=False):
    res = biobase.rowMedians(eset,
                             na_rm=na_rm)
    return res

res = rowmedians(eset_myclass)
```

The R method `rowMedians` is also defined for matrices, which we can expose
on the Python end as well:

```python
from rpy2.robjects.vectors import Matrix
@dispatch(Matrix)
def rowmedians(m,
               na_rm=False):
    res = biobase.rowMedians(m,
                             na_rm=na_rm)
    return res
```

While this is working, one can note that we call the same R function
`rowMedians()` in the package `Biobase` in both Python decorated
functions. What is happening is that the dispatch is performed by R.

If this is ever becoming a performance issue, the specific R function
dispatched can be prefetched and explicitly called in the Python
function. For example:

```python
from rpy2.robjects.methods import getmethod
from rpy2.robjects.vectors import StrVector
_rowmedians_matrix = getmethod(StrVector(["rowMedians"]),
                               signature=StrVector(["matrix"]))
@dispatch(Matrix)
def rowmedians(m,
               na_rm=False):
    res = _rowmedians_matrix(m,
                             na_rm=na_rm)
    return res
```
