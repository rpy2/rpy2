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
