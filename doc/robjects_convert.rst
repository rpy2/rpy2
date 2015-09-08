.. module:: rpy2.robjects.conversion
   :synopsis: Shuttling between low-level and higher(er)-level representations

.. _robjects-conversion:

Mapping rpy2 objects to arbitrary python objects
================================================

.. note::

   Switching between a conversion and a no conversion mode,
   an operation often present when working with RPy-1.x, is no longer
   necessary with `rpy2`.

   The approach followed in `rpy2` has 2 levels (`rinterface` and `robjects`),
   and conversion functions help moving between them.


Protocols
---------

At the lower level (:mod:`rpy2.rinterface`), the rpy2 objects exposing
R objects implement Python protocols to make them feel as natural to a Python
programmer as possible. With them they can be passed as arguments to many
non-rpy2 functions without the need for conversion.

R vectors are mapped to Python objects implementing the methods
:meth:`__getitem__` / :meth:`__setitem__` in the sequence
protocol so elements can be accessed easily. They also implement the Python buffer protocol,
allowing them be used in :mod:`numpy` functions without the need for data copying or conversion.

R functions are mapped to Python
objects implementing the :meth:`__call__` so they can be called just as if
they were functions.

R environments are mapped to Python objects implementing :meth:`__getitem__` / :meth:`__setitem__` in the mapping
protocol so elements can be accessed similarly to in a Python :class:`dict`.

.. note::

   The `rinterface` level is largely implemented in C, bridging Python and R C-APIs.
   There is no easy way to customize it.


Conversion
----------

In its high-level interface :mod:`rpy2` is using a conversion system that has the task of
convertion objects between the following 3 representations:
- lower-level interface to R (:mod:`rpy2.rinterface` level),
- higher-level interface to R (:mod:`rpy2.robjects` level)
- other (no :mod:`rpy2`) representations

 For example, if one wanted have all Python :class:`tuple` turned into R `character` vectors
 (1D arrays of strings) as exposed by `rpy2`'s low-level interface the function would look like:
 
.. code-block:: python

   from rpy2.rinterface import StrSexpVector
   def tuple_str(tpl):
       res = StrSexpVector(tpl)
       return res


Converter objects
^^^^^^^^^^^^^^^^^

The class :class:`rpy2.robjects.conversion.Converter` groups such conversion functions
into one object.

Our conversion function defined above can then be registered as follows:

.. code-block:: python
   
   from rpy2.robjects.conversion import Converter
   my_converter = Converter('my converter')
   my_converter.py2ri.register(tuple, tuple_str)

Converter objects are additive, which can be an easy way to create simple combinations of
conversion rules. For example, creating a converter that adds the rule above to the default
conversion rules is written:

.. code-block:: python
		
   from rpy2.robjects import default_converter
   default_converter + my_converter

Local conversion rules
^^^^^^^^^^^^^^^^^^^^^^

The conversion rules can be customized globally (See section `Customizing the conversion`)
or through the use of local converters as context managers. The latter is
recommended when experimenting or wishing a specific behavior of the conversion
system that is limited in time.

We can use this to example, if we want to change `rpy2`'s current refusal to handle
sequences of unspecified type.

The following code is throwing an error that `rpy2` does not know how to handle
Python sequences.

.. code-block:: python

   x = (1,2,'c')

   from rpy2.robjects.packages import importr
   base = importr('base')

   # error here:
   res = base.paste(x, collapse="-")

This can be changed by using our converter as an addition to the default conversion scheme:

.. code-block:: python

   from rpy2.robjects import default_converter
   from rpy2.robjects.conversion import Converter, localconverter
   with localconverter(default_converter + my_converter) as cv:
       res = base.paste(x, collapse="-")

   
  
:func:`ri2ro`
^^^^^^^^^^^^^

At this level the conversion is between lower-level (:mod:`rpy2.rinterface`)
objects and higher-level (:mod:`rpy2.robjects`) objects.
This method is a generic as implemented in :meth:`functools.singledispatch`
(with Python 2, :meth:`singledispatch.singledispatch`).


:func:`ri2py`
^^^^^^^^^^^^^

At this level the conversion is between lower-level (:mod:`rpy2.rinterface`)
objects and any objects (presumably non-rpy2 is the conversion can be made).
This method is a generic as implemented in :meth:`functools.singledispatch`
(with Python 2, :meth:`singledispatch.singledispatch`).

For example the optional conversion scheme for :mod:`numpy` objects
will return numpy arrays whenever possible.


.. note::

   `robjects`-level objects are also implicitly `rinterface`-level objects
   because of the inheritance relationship in their class definition,
   but the reverse is not true.
   The `robjects` level is an higher level of abstraction, aiming at simplifying
   one's use of R from Python (although at the possible cost of performances).


:func:`p2ri`
^^^^^^^^^^^^^

At this level the conversion is between (presumably) non-rpy2 objects
and rpy2 lower-level (:mod:`rpy2.rinterface`).

This method is a generic as implemented in :meth:`functools.singledispatch`
(with Python 2, :meth:`singledispatch.singledispatch`).


Customizing the conversion
^^^^^^^^^^^^^^^^^^^^^^^^^^

As an example, let's assume that one want to return atomic values
whenever an R numerical vector is of length one. This is only a matter
of writing a new function `ri2py` that handles this, as shown below:

.. code-block:: python

   import rpy2.robjects as robjects
   from rpy2.rinterface import SexpVector
   
   @robjects.conversion.ri2ro.register(SexpVector)
   def my_ri2ro(obj):
       if len(obj) == 1:
           obj = obj[0]
       return obj

Then we can test it with:

>>> pi = robjects.r.pi
>>> type(pi)
<type 'float'>

At the time of writing :func:`singledispath` does not provide a way to `unregister`.
Removing the additional conversion rule without restarting Python is left as an
exercise for the reader.

.. warning::

   The example is bending a little the rpy2 rules, as it is using `ri2ro` while it does not
   return an `robjects` instance when an R vector of length one. We are getting away with it
   because atomic Python types such as :class:`int`, :class:`float`, :class:`bool`, :class:`complex`,
   :class:`str` are well handled by rpy2 at the `rinterface`/C level.
