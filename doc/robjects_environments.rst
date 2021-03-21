.. _robjects-environments:

Environments
============

R environments can be described to the Python user as
an hybrid of a dictionary and a scope.

The first of all environments is called the Global Environment,
that can also be referred to as the R workspace.

An R environment in RPy2 can be seen as a kind of Python
dictionnary.

Assigning a value to a symbol in an environment has been
made as simple as assigning a value to a key in a Python
dictionary:

>>> robjects.r.ls(globalenv)
>>> robjects.globalenv["a"] = 123
>>> print(robjects.r.ls(globalenv))

Care must be taken when assigning objects into an environment
such as the Global Environment, as this can hide other objects
with an identical name.
The following example should make one measure that this can mean
trouble if no care is taken:

>>> globalenv["pi"] = 123
>>> print(robjects.r.pi)
[1] 123
>>>
>>> robjects.r.rm("pi")
>>> print(robjects.r.pi)
[1] 3.1415926535897931

The class inherits from the class
:class:`rpy2.rinterface.SexpEnvironment`.

An environment is also iter-able, returning all the symbols
(keys) it contains:

>>> env = robjects.r.baseenv()
>>> [x for x in env]
<a long list returned>

.. note:: 

   Although there is a natural link between environment
   and R packages, one should consider using the convenience wrapper
   dedicated to model R packages (see :ref:`robjects-packages`).
   
.. autoclass:: rpy2.robjects.Environment(o=None)
   :show-inheritance:
   :members:

Environments as (temporary) local contexts
------------------------------------------

Environments are like nested boxes, each with an arbritrary number of
symbols (the objects names) bound to objects (the actual code or data
associated with the symbol). The topmost environment is `globalenv`
(`.GlobalEnv` in R).

When looking for a symbol, R will normally start looking for it in a starting
environment, and if it does not find it it will look for it the
enclosing (parent) environment. This is will repeat until the symbol
is found or `globalenv` is reached and there is no more environment to search.

The evaluation of R code can be given a starting environment, and this
can be an alternative from cluttering `globalenv`.

To illustrate this, we have an R code that adds one to
a value `y` it has to find somewhere in its evaluation context.

>>> res = robjects.r('y + 1')
RRuntimeError: Error in (function (expr, envir = parent.frame(), enclos = if (is.list(envir) ||  : 
  object 'y' not found

Evaluating that code when no `y` can be found results in an
error message.


Adding a `y` to `globalenv` solves the issue:

>>> robjects.globalenv['y'] = 2
>>> res = robjects.r('y + 1')
>>> print(res)
[1] 3

This is happening because `globalenv` is the environment where our function
was defined (its closure).

However, we could also an other environment.

There as several mechanisms to do that, and one them is to use
:func:`rpy2.robjects.environments.local_context` (also available
as :func:`rpy2.robjects.local_context`). It provides an easy way to
temporarily set evaluation contexts.

.. code-block:: python

   rsrc = 'y + 1'
   if 'y' in robjects.globalenv:
       del(robjects.globalenv['y'])
   with robjects.local_context() as lc_a:
       lc_a['y'] = 2
       print('In local context a:')
       print(robjects.r(rsrc))
       with robjects.local_context() as lc_b:
           lc_b['y'] = 3
           print('In local context b (masking a):')
           print(robjects.r(rsrc))
       print('Back to local context a:')
       print(robjects.r(rsrc))


The result is::
  

  In local context a:
  [1] 3

  In local context b (masking a):
  [1] 4

  Back to local context a:
  [1] 3

Being able to do this is particularly helpful with R functions that like to report the full data
content when anonymous objects are used. This is the case for a lot of the statistical modeling
code in R's standard library. A local context can help with binding the object to a symbol
while R code is evaluated.

.. note::

   The function :func:`rpy2.robjects.rl` will turn a string into an unevaluated R language
   object. To know more, see Section :ref:`robjects-language`.

.. code-block:: python

   from rpy2.robjects.packages import importr
   from rpy2.robjects import rl

   stats = importr('stats')
   mtcars = robjects.r('mtcars')
   with robjects.local_context() as lc:
       lc['mtcars'] = mtcars
       fit = stats.lm('mpg ~ gear', data=rl('mtcars'))
