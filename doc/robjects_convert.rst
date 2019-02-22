.. module:: rpy2.robjects.conversion
   :synopsis: Converting rpy2 proxies for R objects into Python objects.

.. _robjects-conversion:

Mapping rpy2 objects to arbitrary python objects
================================================


Protocols
---------

At the lower level (:mod:`rpy2.rinterface`), the rpy2 objects exposing
R objects implement Python protocols to make them feel as natural to a Python
programmer as possible. With them they can be passed as arguments to many
non-rpy2 functions without the need for conversion.

R vectors are mapped to Python objects implementing the methods
:meth:`__getitem__` / :meth:`__setitem__` in the sequence
protocol so elements can be accessed easily. They also implement the Python buffer
protocol, allowing them be used in :mod:`numpy` functions without the need for data
copying or conversion.

R functions are mapped to Python objects implementing the :meth:`__call__` so they
can be called just as if they were functions.

R environments are mapped to Python objects implementing :meth:`__getitem__` /
:meth:`__setitem__` in the mapping protocol so elements can be accessed similarly to
in a Python :class:`dict`.

.. note::

   The `rinterface` level is quite close to R's C API and modifying it may quickly
   results in segfaults.


Conversion
----------

In its high-level interface :mod:`rpy2` is using a conversion system that has the task
of convertion objects between the following 3 representations:
- lower-level interface to R (:mod:`rpy2.rinterface` level),
- higher-level interface to R (:mod:`rpy2.robjects` level)
- other (no :mod:`rpy2`) representations

 For example, if one wanted have all Python :class:`tuple` turned into R `character`
 vectors (1D arrays of strings) as exposed by `rpy2`'s low-level interface the function
 would look like:
 
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
   my_converter.py2rpy.register(tuple, tuple_str)

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

   x = (1, 2, 'c')

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


:func:`rpy2py`
^^^^^^^^^^^^^^

The conversion is trying to turn an rpy2 object (either :mod:`rpy2.rinterface` or
:mod:`rpy2.robjects` level, low or high level interface respectively)
into a Python object (or an object that is more Python-like than the input object).
This method is a generic as implemented in :meth:`functools.singledispatch`.

For example the optional conversion scheme for :mod:`numpy` objects
will return numpy arrays whenever possible.

.. note::

   `robjects`-level objects are also implicitly `rinterface`-level objects
   because of the inheritance relationship in their class definitions,
   but the reverse is not true.
   The `robjects` level is an higher level of abstraction, aiming at simplifying
   one's use of R from Python (although at the possible cost of performances).


:func:`py2rpy`
^^^^^^^^^^^^^^

The conversion is between (presumably) non-rpy2 objects
and rpy2 objects. The result tend to be a lower-level interface
object (:mod:`rpy2.rinterface`) because this conversion is often the step before an
object is passed to R.

This method is a generic as implemented in :meth:`functools.singledispatch`
(with Python 2, :meth:`singledispatch.singledispatch`).


Customizing the conversion
^^^^^^^^^^^^^^^^^^^^^^^^^^

As an example, let's assume that one want to return atomic values
whenever an R numerical vector is of length one. This is only a matter
of writing a new function `rpy2py` that handles this, as shown below:

.. code-block:: python

   import rpy2.robjects as robjects
   from rpy2.rinterface import SexpVector
   
   @robjects.conversion.rpy2py.register(SexpVector)
   def my_rpy2py(obj):
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

