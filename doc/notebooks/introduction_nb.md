# Introduction to rpy2


This introduction aims at making a gentle start to rpy2,
either when coming from R to Python/rpy2, from Python to rpy2/R,
or from elsewhere to Python/rpy2/R.


## Getting started

It is assumed here that the rpy2 package has been properly installed.
In python, making a package or module available is achieved by
importing it. `rpy2` is just a python package. Most users will interact
with R using the `robjects` layer, a high-level interface that tries
to hide R behind a Python-like behavior.

```python
import rpy2.robjects as robjects
```

## R packages

R is  any data analysis toolbox because of the
breadth and depth of the packages available.

For this introduction, we use few popular R packages.

```python
# R package names
packnames = ('ggplot2', 'hexbin')

# import rpy2's package module
import rpy2.robjects.packages as rpackages

if all(rpackages.isinstalled(x) for x in packnames):
    have_tutorial_packages = True
else:
    have_tutorial_packages = False
```

Downloading and installing R packages is usually performed
by fetching R packages
from a package repository and installing them locally.
We can get set with:

```python
if not have_tutorial_packages:
    # import R's utility package
    utils = rpackages.importr('utils')
    # select a mirror for R packages
    utils.chooseCRANmirror(ind=1) # select the first mirror in the list
```

We are now ready to install packages using R's own function `install.package`:

```python
if not have_tutorial_packages:
    # R vector of strings
    from rpy2.robjects.vectors import StrVector
    # file
    packnames_to_install = [x for x in packnames if not rpackages.isinstalled(x)]
    if len(packnames_to_install) > 0:
        utils.install_packages(StrVector(packnames_to_install))
```
	   
The code above can be part of the Python you distribute if you are relying
on packages not distributed with
R by default.

More documentation about the handling of R packages in `rpy2` can be found Section :ref:`robjects-packages`.


## The `r` instance


The object `r` in `rpy2.robjects` represents the embedded
`R` process.

If familiar with R and the R console, `r` is a little like a
communication channel from Python to R.


### Getting R objects

In Python the `[` operator is an alias for the  ethod :meth:`__getitem__`.

The :meth:`__getitem__` method of :mod:`rpy2.robjects.r`,
evaluates a variable from the R console.

Example in R:

```python
%load_ext rpy2.ipython
```

```r
pi
```

With :mod:`rpy2`:

```python
pi = robjects.r['pi']
pi[0]
```

<div style="border: solid 1px rgb(50,50,50)">
<p>
   Under the hood, the variable `pi` is gotten by default from the
   R *base* package, unless an other variable with the name `pi` was
   created in R's `.globalEnv`. 
</p>
<p>
   Whenever one wishes to be specific about where the symbol
   should be looked for (which should be most of the time),
   it possible to wrap R packages in Python namespace objects
   (see Section `robjects-packages`).
</p>
<p>
   For more details on environments, see Section 
   `robjects-environments`.
</p>
<p>
   Also, note that *pi* is not a scalar but a vector of length 1.
</p>
</div>

### Evaluating R code

The `r` object is also callable, and the string passed to it evaluated
as `R` code.

This can be used to `get` variables, and provide an alternative to
the method presented above.

Example in R:

```r
pi
```

With `rpy2`:

```python
pi = robjects.r('pi')
pi[0]
```

<div style="border: solid 1px rgb(50,50,50)">

   The result is an R vector. The Section
   `introduction-vectors` will provide an explanation
   for the following behavior:

</div>

```python
piplus2 = robjects.r('pi') + 2
print(piplus2.r_repr())
pi0plus2 = robjects.r('pi')[0] + 2
print(pi0plus2)
```

The evaluation is performed in what is known to R users as the 
`Global Environment`, that is the place one starts at when starting
the R console. Whenever the `R` code creates variables, those
variables are "located" in that `Global Environment` by default.


Example:

```python
robjects.r('''
	f <- function(r, verbose=FALSE) {
        if (verbose) {
            cat("I am calling f().\n")
        }
        2 * pi * r 
        }
        f(3)
''')
```

The expression above returns the value 18.85, 
but first creates an R function `f`. 
That function `f` is present in the R `Global Environement`, and can
be accessed with the `__getitem__` mechanism outlined above:

```python
r_f = robjects.globalenv['f']
print(r_f.r_repr())
```

<div style="border: solid 1px rgb(50,50,50)">

   As shown earlier, an alternative way to get the function
   is to get it from the :class:`R` singleton

   ```
   >>> r_f = robjects.r['f']
   ```

</div>

The function r_f is callable, and can be used like a regular Python function.

```python
res = r_f(3)
```

Jump to Section :ref:`robjects-introduction-functions` for more on calling
functions.


### Interpolating R objects into R code strings

Against the first impression one may get from the title
of this section, simple and handy features of :mod:`rpy2` are
presented here.

An R object has a string representation that can be used
directly into R code to be evaluated.

Simple example:

```python
letters = robjects.r['letters']
rcode = 'paste(%s, collapse="-")' %(letters.r_repr())
res = robjects.r(rcode)
print(res)
```

.. _introduction-vectors:

R vectors
=========

In `R`, data are mostly represented by vectors, even when looking
like scalars.

When looking closely at the R object `pi` used previously,
we can observe that this is in fact a vector of length 1.

>>> len(robjects.r['pi'])
1

As such, the python method :meth:`add` will result in a concatenation
(function `c()` in R), as this is the case for regular python lists.

Accessing the one value in that vector has to be stated
explicitly:

>>> robjects.r['pi'][0]
3.1415926535897931

There is much that can be achieved with vectors, having them to behave
more like Python lists or R vectors.
A comprehensive description of the behavior of vectors is found in
:mod:`robjects.vector`.

Creating rpy2 vectors
---------------------

Creating R vectors can be achieved simply:

>>> res = robjects.StrVector(['abc', 'def'])
>>> print(res.r_repr())
c("abc", "def")
>>> res = robjects.IntVector([1, 2, 3])
>>> print(res.r_repr())
1:3
>>> res = robjects.FloatVector([1.1, 2.2, 3.3])
>>> print(res.r_repr())
c(1.1, 2.2, 3.3)

R matrixes and arrays are just vectors with a `dim` attribute.

The easiest way to create such objects is to do it through
R functions:

>>> v = robjects.FloatVector([1.1, 2.2, 3.3, 4.4, 5.5, 6.6])
>>> m = robjects.r['matrix'](v, nrow = 2)
>>> print(m)
     [,1] [,2] [,3]
[1,]  1.1  3.3  5.5
[2,]  2.2  4.4  6.6


.. _robjects-introduction-functions:

Calling R functions
===================

Calling R functions is disappointingly similar to calling
Python functions:

>>> rsum = robjects.r['sum']
>>> rsum(robjects.IntVector([1,2,3]))[0]
6L

Keywords are also working:

>>> rsort = robjects.r['sort']
>>> res = rsort(robjects.IntVector([1,2,3]), decreasing=True)
>>> print(res.r_repr())
c(3L, 2L, 1L)


.. note::

   By default, calling R functions returns R objects.


More information on functions is in Section :ref:`robjects-functions`.


Getting help
============

R has a builtin help system that, just like the pydoc strings are used frequently
in python during interactive sessions, is used very frequently by R programmmers.
This help system is accessible from an R function, therefore accessible from rpy2.

Help on a topic within a given package, or currently loaded packages
---------------------------------------------------------------------

>>> from rpy2.robjects.packages import importr
>>> utils = importr("utils") 
>>> help_doc = utils.help("help")
>>> help_doc[0]
'/where/R/is/installed/library/utils/help/help'

Converting the object returned to a string produces the full help text
on the topic:

>>> str(help_doc)
[...long output...]

.. warning::

   The help message so produced is not a string returned to the console
   but is directly printed by R to the standard output. The call to
   :func:`str` only returns an empty string, and the reason for this is
   somewhat involved for an introductory documentation.
   This behaviour is rooted in :program:`R` itself and in :mod:`rpy2` the
   string representation of R objects is the string representation as
   given by the :program:`R` console,
   which in that case takes a singular route.

   For a Python friendly help to the R help system, consider the module
   :mod:`rpy2.robjects.help`.


Locate topics among available packages
--------------------------------------

>>> help_where = utils.help_search("help")

As before with `help`, the result can be printed / converted to a string,
giving a similar result to what is obtained from an R session.

.. note::

   The data structure returned can otherwise be used to access the information
   returned in details.

   >>> tuple(help_where)
   (<StrVector - Python:0x1f9a968 / R:0x247f908>,
    <StrVector - Python:0x1f9a990 / R:0x25079d0>,
    <StrVector - Python:0x1f9a9b8 / R:0x247f928>,
    <Matrix - Python:0x1f9a850 / R:0x1ec0390>)
   >>> tuple(help_where[3].colnames)
   ('topic', 'title', 'Package', 'LibPath')

   However, this is beyond the scope of an introduction, and one should
   master the content of the module :mod:`robjects.vector` before anything else.


Examples
========

This section demonstrates some of the features of
rpy2.


Graphics and plots
------------------

.. code-block:: python

  import rpy2.robjects as robjects

  r = robjects.r

  x = robjects.IntVector(range(10))
  y = r.rnorm(10)

  r.X11()

  r.layout(r.matrix(robjects.IntVector([1,2,3,2]), nrow=2, ncol=2))
  r.plot(r.runif(10), y, xlab="runif", ylab="foo/bar", col="red")

Setting dynamically the number of arguments in a function call can be
done the usual way in python.

There are several ways to plot data in `R`, some of which are
presented in this documentation:

The general setup is repeated here:

.. literalinclude:: _static/demos/graphics.py
   :start-after: #-- setup-begin
   :end-before: #-- setup-end

The setup specific to ggplot2 is:

.. literalinclude:: _static/demos/graphics.py
   :start-after: #-- setupggplot2-begin
   :end-before: #-- setupggplot2-end

.. literalinclude:: _static/demos/graphics.py
   :start-after: #-- ggplot2smoothbycylwithcolours-begin
   :end-before: #-- ggplot2smoothbycylwithcolours-end

   
.. image:: _static/graphics_ggplot2_smoothbycylwithcolours.png
   :scale: 50

More about plots and graphics in R, as well as more advanced
plots are presented in Section :ref:`graphics`.

.. warning::

   By default, the embedded R open an interactive plotting device,
   that is a window in which the plot is located.
   Processing interactive events on that devices, such as resizing or closing
   the window must be explicitly required
   (see Section :ref:`rinterface-interactive-processevents`).

Linear models
-------------

The R code is:

.. code-block:: r

   ctl <- c(4.17,5.58,5.18,6.11,4.50,4.61,5.17,4.53,5.33,5.14)
   trt <- c(4.81,4.17,4.41,3.59,5.87,3.83,6.03,4.89,4.32,4.69)
   group <- gl(2, 10, 20, labels = c("Ctl","Trt"))
   weight <- c(ctl, trt)

   anova(lm.D9 <- lm(weight ~ group))

   summary(lm.D90 <- lm(weight ~ group - 1))# omitting intercept

One way to achieve the same with :mod:`rpy2.robjects` is

.. code-block:: python

   from rpy2.robjects import FloatVector
   from rpy2.robjects.packages import importr
   stats = importr('stats')
   base = importr('base')

   ctl = FloatVector([4.17,5.58,5.18,6.11,4.50,4.61,5.17,4.53,5.33,5.14])
   trt = FloatVector([4.81,4.17,4.41,3.59,5.87,3.83,6.03,4.89,4.32,4.69])
   group = base.gl(2, 10, 20, labels = ["Ctl","Trt"])
   weight = ctl + trt

   robjects.globalenv["weight"] = weight
   robjects.globalenv["group"] = group
   lm_D9 = stats.lm("weight ~ group")
   print(stats.anova(lm_D9))

   # omitting the intercept
   lm_D90 = stats.lm("weight ~ group - 1")
   print(base.summary(lm_D90))

This way to perform a linear fit it matching precisely the way in R presented
above, but there are other ways (see Section :ref:`robjects-formula`
for storing the variables directly in the lookup environment of the formula).

Q: Now how to extract data from the resulting objects ?

A: Well, it all depends on the object. R is very much designed
for interactive sessions, and users often inspect what a
function is returning in order to know how to extract information.

When taking the results from the code above, one could go like:

>>> print(lm_D9.rclass)
[1] "lm" 

Here the resulting object is a list structure, as either inspecting
the data structure or reading the R man pages for `lm` would tell us.
Checking its element names is then trivial:

>>> print(lm_D9.names)
 [1] "coefficients"  "residuals"     "effects"       "rank"         
 [5] "fitted.values" "assign"        "qr"            "df.residual"  
 [9] "contrasts"     "xlevels"       "call"          "terms"        
[13] "model" 

And so is extracting a particular element:

>>> print(lm_D9.rx2('coefficients'))
(Intercept)    groupTrt 
      5.032      -0.371 

or 

>>> print(lm_D9.rx('coefficients'))
$coefficients
(Intercept)    groupTrt 
      5.032      -0.371 

More about extracting elements from vectors is available
at :ref:`robjects-extracting`.


   
Principal component analysis
----------------------------

The R code is

.. code-block:: r

  m <- matrix(rnorm(100), ncol=5)
  pca <- princomp(m)
  plot(pca, main="Eigen values")
  biplot(pca, main="biplot")

The :mod:`rpy2.robjects` code can be as close to the
R code as possible:

.. testcode::

  import rpy2.robjects as robjects

  r = robjects.r

  m = r.matrix(r.rnorm(100), ncol=5)
  pca = r.princomp(m)
  r.plot(pca, main="Eigen values")
  r.biplot(pca, main="biplot")

However, the same example can be made a little tidier
(with respect to being specific about R functions used)

.. testcode::

   from rpy2.robjects.packages import importr

   base     = importr('base')
   stats    = importr('stats')
   graphics = importr('graphics')

   m = base.matrix(stats.rnorm(100), ncol = 5)
   pca = stats.princomp(m)
   graphics.plot(pca, main = "Eigen values")
   stats.biplot(pca, main = "biplot") 



Creating an R vector or matrix, and filling its cells using Python code
-----------------------------------------------------------------------

.. testcode::

   from rpy2.robjects import NA_Real
   from rpy2.rlike.container import TaggedList
   from rpy2.robjects.packages import importr

   base = importr('base')

   # create a numerical matrix of size 100x10 filled with NAs 
   m = base.matrix(NA_Real, nrow=100, ncol=10)

   # fill the matrix
   for row_i in xrange(1, 100+1):
       for col_i in xrange(1, 10+1):
           m.rx[TaggedList((row_i, ), (col_i, ))] = row_i + col_i * 100

.. testoutput::

   None

One more example
----------------

.. literalinclude:: _static/demos/example01.py

