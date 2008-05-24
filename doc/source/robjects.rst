*************
rpy2.robjects
*************

Overview
========

This module is intended for casual and general use.
Its aim is to abstracts some of the details and provide an
intuitive interface to R.


>>> import rpy2.robjects as robjects


:mod:`robjects` is written on the top of :mod:`rinterface`, and one
not satisfied with it could easily build one's own flavor of a
Python-R interface by modifying it.

Classes
=======

:class:`Robject`
  Parent class for R objects.

:class:`Rvector`
  An R vector

:class:`Renvironment`
  An R environment.

:class:`Rfunction`
  An R function.


R
-

This class is currently a singleton, with
its one representation instanciated when the
module is loaded:

>>> robjects.r
>>> print(robjects.r)

The instance can be seen as a window to an
embedded R process.
Readers familiar with the ctypes module for Python

R vectors:

>>> pi = robjects.r.pi
>>> letters = robjects.r.letters


R functions:

>>> plot = robjects.r.plot
>>> dir = robjects.r.dir

The evaluation of R code in a string can also be performed
FIXME: (not yet implemented/tested)

:class:`Robject`
----------------

:class:`Rvector`
----------------

Beside functions, and environemnts, most of the objects
an R user is interacting with are vector-like.
For example, this means that any scalar is in fact a vector
of length one.

The class :class:`Rvector` has a constructor:

>>> x = robjects.Rvector(3)


Mathematical operations on vectors: the following operations
are performed element-wise, recycling the shortest vector if
necessary.

+-------+---------+
| ``+`` | Add     |
+-------+---------+
| ``-`` | Subtract|
+-------+---------+
| ``*`` | Multiply|
+-------+---------+
| ``/`` | Divide  |
+-------+---------+

FIXME:
Indexing

This class is using the class :class:`rinterface.SexpVector`.

Numpy, Numeric

Vectors are understood as Numpy or Numeric arrays::

  import numpy
  ltr = robjects.r.letters
  ltr_np = numpy.array(ltr)




:class:`Renvironment`
---------------------

R environments can be described to the Python user as
an hybrid of a dictionary and a scope.

The first of all environments is called the Global Environment,
that can also be referred to as the R workspace.

>>> globalEnv = robjects.globalEnv


An R environment in RPy2 can be seen as a kind of Python
dictionnary.

Assigning a value to a symbol in an environment has been
made as simple as assigning a value to a key in a Python
dictionary:

>>> robjects.r.ls(globalEnv)
>>> globalEnv["a"] = 123
>>> robjects.r.ls(globalEnv)


Care must be taken when assigning objects into an environment
such as the Global Environment, as it can hide other objects
with an identical name.
For example:

>>> globalEnv["pi"] = 123
>>> robjects.r.pi
123L
>>>

>>> robjects.r.rm("pi")
>>> robjects.r.pi
3.1415926535897931

This class is using the class :class:`rinterface.SexpEnvironment`

An environment is also iter-able, returning all the symbols
(keys) it contains:

>>> env = robjects.r.baseenv()
>>> len([x for x in env])


:class:`Rfunction`
------------------

>>> plot = robjects.r.plot
>>> rnorm = robjects.r.rnorm
>>> plot(rnorm(100), ylab="random")

This class is using the class :class:`rinterface.SexpClosure`


Mapping
-------

The mapping between low-level objects is performed by the
functions XXX and XXX.

A developper can easily add his own mapping XXX.


Examples
========

Example::

  import array

  r = robjects.r

  x = array.array('i', range(10))
  y = r.rnorm(10)

  r.X11()

  r.par(mfrow=array.array('i', [2,2]))
  r.plot(x, y, ylab="foo/bar", col="red")

  kwargs = {'ylab':"foo/bar", 'type':"b", 'col':"blue", 'log':"x"}
  r.plot(x, y, **kwargs)

Principal component analysis
----------------------------

.. code-block:: r

  m <- matrix(rnorm(100), ncol=5)
  pca <- princomp(m)
  plot(pca, main="Eigen values")
  biplot(pca, main="biplot")

.. code-block:: python

  m = r.matrix(r.rnorm(100), ncol=5)
  pca = r.princomp(m)
  r.plot(pca, main="Eigen values")
  r.biplot(pca, main="biplot")


S4 classes
----------

.. code-block:: python

  if not r.require("GO")[0]:
      raise(Exception("Bioconductor Package GO missing"))

  goItem = r.GOTERM["GO:0000001"]

