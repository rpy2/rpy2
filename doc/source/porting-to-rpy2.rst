Porting code to rpy2
====================


From R
------

From rpy
--------

Compatibility layer
^^^^^^^^^^^^^^^^^^^

A compatibility layer exists, although it currently does not implement
completely the rpy interface.

Faithful example
^^^^^^^^^^^^^^^^

In years, Tim Church's *Old faithful* example seems to have reached an 
almost iconic status for many :mod:`rpy` users. 
That example is the obvious text for a Rosetta stone and we provide
its translation into :mod:`rpy2.robjects` for rpy2-2.1.0. This example
is based on John A. Schroeder's translation for rpy2-2.0.8 (that is
also working with version 2.1, but cannot use new features for obvious
compatibility reasons).


Setting up
""""""""""

rpy2 can hide more of the R layer, providing an interface that only
requires Python knowledge.

.. code-block:: python

   from rpy2.robjects.vectors import DataFrame
   from rpy2.robjects.packages import importr

   r_base = importr('base')

The example only uses explicitly a :class:`rpy2.robjects.vectors.DataFrame`, and
defined R packages. The function :func:`rpy2.robjects.packages.importr` allows
the encapsulation of R functions in packages into a Python-friendly form.


Importing the data
""""""""""""""""""

.. code-block:: python

   faithful_data = DataFrame.from_csvfile('faithful.dat', sep = " ")

If you do not have the data file nearby, this dataset can be loaded from
R's own collection of datasets:

.. code-block:: python

   datasets = importr('datasets')
   faithful_data = datasets.faithful

Summary
"""""""

.. code-block:: python

   edsummary = r_base.summary(faithful_data.rx2("eruptions"))
   for k, v in edsummary.iteritems():
      print("%s: %.3f\n" %(k, v))

Stem-and-leaf plot
""""""""""""""""""

.. code-block:: python

   graphics = importr('graphics')

   print("Stem-and-leaf plot of Old Faithful eruption duration data")
   graphics.stem(faithful_data.rx2("eruptions"))

Histogram
"""""""""

.. code-block:: python

   grdevices = importr('grDevices')
   stats = importr('stats')
   grdevices.png('faithful_histogram.png', width = 733, height = 550)
   ed = faithful_data.rx2("eruptions")
   graphics.hist(ed, r_base.seq(1.6, 5.2, 0.2), 
                 prob = True, col = "lightblue",
                 main = "Old Faithful eruptions", xlab = "Eruption duration (seconds)")
   graphics.lines(stats.density(ed,bw=0.1), col = "orange")
   graphics.rug(ed)
   grdevices.dev_off()

Alternatively, the ggplot2 package can be used to make the plots:

.. code-block:: python

   from rpy2.robjects.lib import ggplot2

   p = ggplot2.ggplot(faithful_data) + \
       ggplot2.aes_string(x = "eruptions") + \
       ggplot2.geom_histogram(fill = "lightblue") + \
       ggplot2.geom_density(ggplot2.aes_string(y = '..count..'), colour = "orange") + \
       ggplot2.geom_rug() + \
       ggplot2.scale_x_continuous("Eruption duration (seconds)") + \
       ggplot2.opts(title = "Old Faithful eruptions")

   p.plot()

.. code-block:: python

   from rpy2.robjects.vectors import FloatVector

   long_ed = FloatVector([x for x in ed if x > 3])
   grdevices.png('faithful_ecdf.png', width = 733, height = 550)

   stats = importr('stats')

   params = {'do.points' : False, 
             'verticals' : 1, 
             'main' : "Empirical cumulative distribution function of " + \
                       "Old Faithful eruptions longer than 3 seconds"}
   graphics.plot(stats.ecdf(long_ed), **params)
   x = r_base.seq(3, 5.4, 0.01)
   graphics.lines(x, stats.pnorm(x, mean = r_base.mean(long_ed), 
                                 sd = r_base.sqrt(stats.var(long_ed))),
                  lty = 3, lwd = 2, col = "salmon")
   grdevices.dev_off()

.. code-block:: python
    
   grdevices.png('faithful_qq.png', width = 733, height = 550)
   graphics.par(pty="s")
   stats.qqnorm(long_ed,col="blue")
   stats.qqline(long_ed,col="red") # strangely in stats, not in graphics
   grdevices.dev_off()



From rpy2-2.0.x
---------------

This section refers to changes in the :mod:`rpy2.objects` layer.
If interested in changes to the lower level :mod:`rpy2.rinterface`,
the list of changes in the appendix should be consulted.

Camelcase
^^^^^^^^^

The camelCase naming disappeared from variables and methods, as it seemed
to be mostly absent from such obejcts in the standard library
(although nothing specific appears about that in :pep:`8`).

Practically, this means that the following name changes occurred:

+----------------------+-------------+
| old name             | new name    |
+======================+=============+
| :mod:`rpy2.robjects`               |
+----------------------+-------------+
| `globalEnv`          | `globalenv` |
+----------------------+-------------+
| `baseNameSpaceEnv`   | `baseenv`   |
+----------------------+-------------+
| :mod:`rpy2.rinterface`             |
+----------------------+-------------+
| `globalEnv`          | `globalenv` |
+----------------------+-------------+
| `baseEnv`            | `baseenv`   |
+----------------------+-------------+


R-prefixed class names
----------------------

Class names prefixed with the letter `R` were cleaned from that prefix.
For example, `RVector` became `Vector`, `RDataFrame` became `DataFrame`, etc...

+---------------+--------------+
| old name      | new name     |
+===============+==============+
| :mod:`rpy2.robjects`         |
+---------------+--------------+
| `RVector`     | `Vector`     |
+---------------+--------------+
| `RArray`      | `Array`      |
+---------------+--------------+
| `RMatrix`     | `Matrix`     |
+---------------+--------------+
| `RDataFrame`  | `DataFrame`  |
+---------------+--------------+
| `REnvironment`| `Environment`|
+---------------+--------------+
| `RFunction`   | `Function`   |
+---------------+--------------+
| `RFormula`    | `Formula`    |
+---------------+--------------+


Namespace for R packages
^^^^^^^^^^^^^^^^^^^^^^^^

The function :func:`rpy2.robjects.packages.importr` should be used to import an R package
name space as a Python-friendly object

>>> from rpy2.robjects.packages import importr
>>> base = importr("base")
>>> base.letters[0]
'a'

Whenever possible, this steps performs a safe 
conversion of '.' in R variable names into '_' for the Python variable
name.

The documentation in Section :ref:`robjects-packages` gives more details.

Parameter names in function call
---------------------------------

By default, R functions exposed will have a safe translation of their named parameters
attempted ('.' will become '_'). Section :ref:`robjects-functions` should be checked for
details.


Missing values
---------------

R has a built-in concept of *missing values*, and of types for missing values.
This now better integrated into rpy2 (see Section :ref:`robjects-missing_values`)

Graphics
--------

The combined use of namespaces for R packages (see above),
and of custom representation of few specific R libraries is making
the generation of graphics (even) easier (see Section :ref:`graphics`).

