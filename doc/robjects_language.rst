
.. index::
   pair: robjects; LangVector

.. _robjects-language:

R language
==========

Beside its syntax, R differs from Python in the way expressions are evaluated.
In R the evaluation is deferred until the result of the expression is needed,
while in Python the evaluation when the execution is going through the expression.

For example, this means that expression that arguments to R functions will see their
evaluation deferred until when the code in the body of the function is evaluated.
The R package `dplyr` relies on this feature heavily. One can write

.. code-block:: r

   ## data is a data frame with a column called "x".
   ## To filter rows with positive values in column "x" we can do:
   filter(data, x > 0)

and just works because the expression `x > 0` is carefully evaluated within
the context of the data frame `data`. At the moment of the call `x > 0` is
otherwise only an unevaluated language object.

In rpy2, the class :class:`rpy2.robjects.language.LangVector` represents such objects.
The constructor that builds them from strings is :meth:`rpy2.robjects.language.LangVector.from_string`,
and is otherwise aliased as :func:`rpy2.robjects.rl`

Should you find yourself unsure about how to represent a particular R idiom in Python,
you can create a language object from a string with what the R code would be. This approach
can sometimes be the easiest way to use R packages that rely on a lot of seemingly magic
with unevaluated expression. That's the case for a lot of packages in the R "tidyverse"
(`dplyr`, `tidyr`, `ggplot2`, etc...). The documentation for the rpy2 mapping for `dplyr`
shows many examples (see Section :ref:`robjects-lib-dplyr`).

