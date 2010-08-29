
.. index::
   pair: robjects; Formula
   single: formula

.. _robjects-formula:

Formulae
========

For tasks such as modelling and plotting, an R formula can be
a terse, yet readable, way of expressing what is wanted.

In R, it generally looks like:

.. code-block:: r

  x <- 1:10
  y <- x + rnorm(10, sd=0.2)

  fit <- lm(y ~ x) 

In the call to `lm`, the argument is a `formula`, and it can read like
*model y using x*.
A formula is a `R` language object, and the terms in the formula
are evaluated in the environment it was defined in. Without further
specification, that environment is the environment in which the
the formula is created.

The class :class:`robjects.Formula` is representing an `R` formula.

.. code-block:: python

  x = robjects.Vector(array.array('i', range(1, 11)))
  y = x.ro + rnorm(10, sd=0.2)

  fmla = robjects.Formula('y ~ x')
  env = fmla.environment
  env['x'] = x
  env['y'] = y

  stats = importr('lm')
  fit = stats.lm(fmla)

One drawback with that approach is that pretty printing of
the `fit` object is note quite as clear as what one would
expect when working in `R`.
However, by evaluating R code on
the fly, we can obtain a `fit` object that will display
nicely:

.. code-block:: python

   fit = robjects.r('lm(%s)' %fmla.r_repr())

.. autoclass:: rpy2.robjects.Formula(formula, environment = rinterface.globalenv)
   :show-inheritance:
   :members:


