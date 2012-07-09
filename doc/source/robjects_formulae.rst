
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
A formula is a :program:`R` language object, and the terms in the formula
are evaluated in the environment it was defined in. Without further
specification, that environment is the environment in which the
the formula is created.

The class :class:`robjects.Formula` is representing an :program:`R` formula.

.. code-block:: python

  import array
  from rpy2.robjects import IntVector, Formula
  from rpy2.robjects.packages import importr
  stats = importr('stats')

  x = IntVector(range(1, 11))
  y = x.ro + stats.rnorm(10, sd=0.2)

  fmla = Formula('y ~ x')
  env = fmla.environment
  env['x'] = x
  env['y'] = y

  fit = stats.lm(fmla)

One drawback with that approach is that pretty printing of
the `fit` object is note quite as good as what one would
expect when working in :program:`R`: the `call` item now displays the code
for the function used to perform the fit.

If one still wants to avoid polluting the R global environment,
the answer is to evaluate R call within the environment where the
function is defined.

.. code-block:: python

   from rpy2.robjects import Environment

   eval_env = Environment()
   eval_env['fmla'] = fmla
   base = importr('base')

   fit = base.eval.rcall(base.parse(text = 'lm(fmla)'), stats._env)


Other options are:

- Evaluate R code on the fly so we that model fitting function has a symbol
  in R

  .. code-block:: python

     fit = robjects.r('lm(%s)' %fmla.r_repr())

- Evaluate R code where all symbols are defined

.. autoclass:: rpy2.robjects.Formula(formula, environment = rinterface.globalenv)
   :show-inheritance:
   :members:


