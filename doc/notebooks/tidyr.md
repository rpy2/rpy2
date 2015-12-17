# tidyr in Python

```python
from rpy2.robjects.lib.tidyr import DataFrame
```

(note: `dplyr` is implicitly used by `tidyr`.)

In addition to that, and because this tutorial is in a notebook,
we initialize HTML rendering for R objects (pretty display of
R data frames).

```python
import rpy2.ipython.html
rpy2.ipython.html.init_printing()
```

```python
from collections import OrderedDict
from rpy2.robjects.vectors import (StrVector,
                                   IntVector)
dataf = DataFrame(OrderedDict(x=StrVector(("a", "b", "b")),
                              y=IntVector((3, 4, 5)),
		              z=IntVector((6, 7, 8))))
dataf
```

```python
dataf.spread('x', 'y')
```
**Reuse. Get things done. Don't reimplement.**
