********
Graphics
********

Introduction
============

This section shows how to make R graphics from rpy2, 
using some of the different graphics systems available to R users.

The purpose of this section is to get users going, and be able to figure out
by reading the R documentation how to perform the same plot in rpy2.


.. code-block:: python

   from rpy2 import robjects

   # import an R package
   def rimport(x):
       robjects.baseNameSpaceEnv["require"](x, quietly = True)

   # load an R dataset
   data = robjects.baseNameSpaceEnv.get("data")

   # The R 'print' function
   rprint = robjects.globalEnv.get("print")



Package *lattice*
=================


Introduction
------------

.. code-block:: python

   rimport('lattice')

   xyplot = robjects.baseNameSpaceEnv.get("xyplot")

Scatter plot
------------

.. code-block:: python

   data("mtcars")
   mtcars = robjects.globalEnv["mtcars"]

   xyplot = robjects.baseNameSpaceEnv.get('xyplot')

   formula = robjects.RFormula('mpg ~ wt')
   formula.getenvironment()['mpg'] = mtcars.r['mpg'][0]
   formula.getenvironment()['wt'] = mtcars.r['wt'][0]

   p = xyplot(formula)
   rprint(p)

.. image:: _static/graphics_lattice_xyplot_1.png
   :scale: 50

.. code-block:: python

   p = xyplot(formula, groups = mtcars.r['cyl'][0])
   rprint(p)

.. image:: _static/graphics_lattice_xyplot_2.png
   :scale: 50

.. code-block:: python

   formula = robjects.RFormula('mpg ~ wt | cyl')
   formula.getenvironment()['mpg'] = mtcars.r['mpg'][0]
   formula.getenvironment()['wt'] = mtcars.r['wt'][0]
   formula.getenvironment()['cyl'] = mtcars.r['cyl'][0]

   p = xyplot(formula, layout=robjects.IntVector((3, 1)))
   rprint(p)

.. image:: _static/graphics_lattice_xyplot_3.png
   :scale: 50

Package *ggplot2*
=================

Introduction
------------

.. code-block:: python

   rimport("ggplot2")

   def dparse(x):
       res = robjects.baseNameSpaceEnv["parse"](text = x)
       return res



Plot
----

.. code-block:: python

   qplot = robjects.r["qplot"]

   x = robjects.r.rnorm(5)
   y = x + robjects.r.rnorm(5, sd = 0.2)
   xy = qplot(x, y, xlab="x", ylab="y")

   rprint(xy)

.. image:: _static/graphics_ggplot2_qplot_1.png
   :scale: 50

.. code-block:: python

   data("mtcars")
   mtcars = robjects.globalEnv["mtcars"]

   xy = qplot(dparse("wt"), dparse("mpg"), 
              data = mtcars,
              xlab = "wt", ylab = "mpg")

   rprint(xy)

.. image:: _static/graphics_ggplot2_qplot_2.png
   :scale: 50


.. code-block:: python

   def radd(x, y):
       res = robjects.baseNameSpaceEnv.get("+")(x, y)
       return res

   ggplot = robjects.globalEnv.get("ggplot")
   aes = robjects.globalEnv.get("aes")

   xy = ggplot(mtcars, aes(y = dparse('wt'), x = dparse('mpg')))

   facet_grid = robjects.globalEnv.get("facet_grid")
   p = radd(xy, facet_grid(robjects.RFormula('. ~ cyl')))

   geom_point = robjects.globalEnv.get("geom_point")
   p = radd(p, geom_point())

   rprint(p)
   
.. image:: _static/graphics_ggplot2_ggplot_1.png
   :scale: 50

Adding graphical elements
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   geom_abline = robjects.globalEnv.get("geom_abline")

   line = geom_abline(intercept = 20) 

   def radd(x, y):
       res = robjects.baseNameSpaceEnv.get("+")(x, y)
       return res

   p = radd(xy, line)

   rprint(p)
   
   p = radd(p, geom_abline(intercept = 15))
   rprint(p)

   stat_smooth = robjects.globalEnv.get("stat_smooth")

   p = radd(p, stat_smooth(method = "lm"))

   p = radd(p, stat_smooth(method = "lm", fill="blue", colour="#e03030d0", size=3))
   
   stat_smooth = robjects.globalEnv.get("stat_smooth")

   p = radd(xy, stat_smooth(method=dparse(lm)))

