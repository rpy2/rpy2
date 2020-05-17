.. module:: rpy2.robjects.conversion
   :synopsis: Converting rpy2 proxies for R objects into Python objects.

.. _robjects-conversion:

Mapping rpy2 objects to arbitrary python objects
================================================


Protocols
---------

At the lower level (:mod:`rpy2.rinterface`), the rpy2 objects wrapping
R objects implement Python protocols to make them feel as natural to a Python
programmer as possible, and in many cases allow to use them with non-R or non-rpy2
functions without the need for conversion.

For example, R vectors are mapped to Python objects implementing the methods
:meth:`__len_`, :meth:`__getitem__`, :meth:`__setitem__` defined in the sequence
protocol. Python functions working with sequences can then be passed such R
objects:

.. code-block::

   import rpy2.rinterface as ri
   ri.initr()

   # R array of integers
   r_vec = ri.IntSexpVector([1,2,3])

   # enumerate() can use our r_vec
   for i, elt in enumerate(r_vec):
       print('r_vec[%i]: %i' % (i, elt))


rpy2 objects with compatible underlying C representations also implement
the :mod:`numpy` :attr:`__array_interface__`, allowing them be used in
:mod:`numpy` functions without the need for datacopying or conversion.

.. note::

   Before the move to :mod:`cffi` Python's buffer protocol was also implemented
   but the Python does not allow classes to define it outside of the Python C-API,
   and `cffi` does not allow the use of the Python's C-API.

   Some rpy2 vectors will have a method :meth:`memoryview` that will return
   views that implement the buffer protocol.

R functions are mapped to Python objects that implement the :meth:`__call__` so they
can be called just as if they were functions.

R environments are mapped to Python objects that implement :meth:`__len__`,
:meth:`__getitem__`, :meth:`__setitem__` in the mapping protocol so elements
can be accessed similarly to in a Python :class:`dict`.

.. warning::

   The `rinterface` level is quite close to R's C API and modifying it may quickly
   result in segfaults.


Conversion
----------

In its high-level interface :mod:`rpy2` is using a conversion system that has the task
of conversion objects between the following 2 representations:
- rpy2 objects, that are proxies to R objects in the embedded R process.
- other (non-rpy2) Python objects. This may cover Python objects in the standard lib,
  or any other Python class defined in additional packages or modules.

The `py2rpy` will indicate a conversion from Python (optionally non-rpy2) to rpy2,
and `rpy2py` from rpy2 to (optionally) non-rpy2.

.. note::

   The rpy2 packages has :mod:`rpy2.robjects.numpy2ri` and :mod:`rpy2.robjects.pandas2ri`
   to convert from and to :mod:`numpy` and :mod:`pandas` objects respectively.
   Sections :ref:`robjects-numpy` and :ref:`robjects-pandas` contain information about
   working with rpy2 and :mod:`numpy` or :mod:`pandas` objects.

As an example of conversion function, if one wanted have all Python :class:`tuple`
turned into R `character`
vectors (1D arrays of strings) as exposed by `rpy2`'s low-level interface the function
would look like:
 
.. code-block:: python

   from rpy2.rinterface import StrSexpVector

   
   def tuple_str(tpl):
       res = StrSexpVector(tpl)
       return res

   
Converter objects
^^^^^^^^^^^^^^^^^

rpy2's conversion system is relying on single dispatch as implemented in
:meth:`functools.singledispatch`. This means that a conversion function,
such as the example function `tuple_str` above, will be associated with
the Python class for which the function should be called.
In our example, the Python class is :class:`tuple` because we want to use it
when an incoming object is a tuple, and our function is written to handle tuples
and return an rpy2 object.
   
The class :class:`rpy2.robjects.conversion.Converter` groups conversion rules
into one object. This helps will defining sets of coherent conversion rules, or
conversion domains. The conversions utilities for :mod:`numpy` or :mod:`pandas`
mentioned above are examples of such converters.

The dispatch functions for "(optionally) non-rpy2 to rpy2" and
"rpy2 to (optionally) non-rpy2" are
:attr:`rpy2.robjects.converters.Converter.py2rpy` and
:attr:`rpy2.robjects.converters.Converter.rpy2py` respectively.

Our conversion function defined above can be registered in a converter as follows:

.. code-block:: python
   
   from rpy2.robjects.conversion import Converter
   seq_converter = Converter('sequence converter')
   seq_converter.py2rpy.register(tuple, tuple_str)

Conversion set of rules in converter objects be layered on the top of one another,
to create sets of combined conversion rules. To help with writing concise and
clear code, :class:`Converter` objects can be added. For example, creating a
converter that adds the rule above to the default conversion rules in rpy2
will look like:

.. code-block:: python
		
   from rpy2.robjects import default_converter
   conversion_rules = default_converter + seq_converter

.. note::

   While a dispatch solely based on Python classes will work very well in the
   direction "non-rpy2 to rpy2" it will show limits in the direction
   "rpy2 to non-rpy2" when stepping out of simple cases,
   or when independently-developed are combined.

   The direction "rpy2 to non-rpy2" is not working so well in those cases
   because rpy2 classes are mirroring the type of R objects at the C-level (as
   defined in R's C-API). However, class definitions in R often sit outside
   of structures found at the C level, and as a mere attribute of the R object
   that contains class names. For example, an R `data.frame` is a `LISTSXP` at
   C-level, but it has an attribute `"class"` that says `"data.frame"`. Nothing
   would prevent someone to set the `"class"` attribute to `"data.frame"`
   to an R object of different type at C-level.

   In order to resolve that duality of class definitions, the rpy2 conversion system can
   optionally defer the final dispatch to a second-stage dispatch.
   
   The attribute :attr:`rpy2.robjects.conversion.Converter.rpy2py_nc_name` is
   mapping an rpy2 type to a :class:`rpy2.robjects.conversion.NameClassMap` that
   resolves a sequence of R class names to the matching conversion
   function.

   For example, a conversion rule for R objects of class "lm" that are R lists at
   the C level (this is a real exemple - R's linear model fit objects are just that)
   can be added to a converter with:

   .. code-block:: python

      class Lm(rinterface.ListSexpVector):
          # implement attributes, properties, methods to make the handling of
	  # the R object more convenient on the Python side
	  pass

      clsmap = myconverter.rpy2py_nc_name[rinterface.ListSexpVector]
      clsmap.update({'lm': Lm})
   
   
Local conversion rules
^^^^^^^^^^^^^^^^^^^^^^

The conversion rules can be customized globally (See section `Customizing the conversion`)
or through the use of local converters as context managers.

.. note::

   The use of local conversion rules is
   much recommended as modifying the global conversion rules can lead to wasted resources
   (e.g., unnecessary round-trip conversions if the code is successively passing results from
   calling R functions to the next R functions) or errors (conversion cannot be guaranteed to
   be without loss, as concepts present in either language are not always able to survive
   a round trip).
   
As an example, we show how to write an alternative to rpy2 not knowing what to do with
Python tuples.

.. code-block:: python

   x = (1, 2, 'c')

   from rpy2.robjects.packages import importr
   base = importr('base')

   # error here:
   # NotImplementedError: Conversion 'py2rpy' not defined for objects of type '<class 'tuple'>'
   res = base.paste(x, collapse="-")

This can be changed by using our converter defined above as an addition to the
default conversion scheme:

.. code-block:: python

   from rpy2.robjects import default_converter
   from rpy2.robjects.conversion import Converter, localconverter
   with localconverter(conversion_rules) as cv:
       res = base.paste(x, collapse="-")

.. note::

   A local conversion rule can also ensure that code is robust against arbitrary changes
   in the conversion system made by the caller.

   For example, to ensure that a function always uses rpy2's default conversion,
   irrespective of what are the conversion rules defined by the caller of the code:

   .. code-block:: python

      from rpy2.robjects import default_converter
      from rpy2.robjects.conversion import localconverter

      def my_function(obj):
          with localconverter(default_converter) as cv:
              # block of code mixing Python code and calls to R functions
	      # interacting with the objects returned by R in the Python code
	      pass


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

.. note::

   Customizing the conversion of S4 classes should preferably done using a separate
   dedicated system.

   The system is rather simple and can easily be described with an example.

   .. code-block:: python

      import rpy2.robjects as robjects
      from rpy2.robjects.packages import importr

      class LMER(robjects.RS4):
          """Custom class."""
          pass

      lme4 = importr('lme4')

      res = robjects.r('lmer(Reaction ~ Days + (Days | Subject), sleepstudy)')

      # Map the R/S4 class 'lmerMod' to our Python class LMER.
      with robjects.conversion.converter.rclass_map_context(
          rinterface.rinterface.SexpS4,
	  {'lmerMod': LMER}
      ):
          res2 = robjects.r('lmer(Reaction ~ Days + (Days | Subject), sleepstudy)')

   When running the example above, `res` is an instance of class
   :class:`rpy2.robjects.methods.RS4`,
   which is the default mapping for R `S4` instances, while `res2` is an instance of our
   custom class `LMER`.

   The class mapping is using the hierarchy of R/S4-defined classes and tries to find
   the first
   matching Python-defined class. For example, the R/S4 class `lmerMod` has a parent class
   `merMod` (defined in R S4). Let run the following example after the previous one.
   
   .. code-block:: python

      class MER(robjects.RS4):
          """Custom class."""
          pass

      with robjects.conversion.converter.rclass_map_context(
          rinterface.rinterface.SexpS4,
	  {'merMod': MER}
      ):
          res3 = robjects.r('lmer(Reaction ~ Days + (Days | Subject), sleepstudy)')

      with robjects.conversion.converter.rclass_map_context(
          rinterface.rinterface.SexpS4,
	  {'lmerMod': LMER,
           'merMod': MER}):
          res4 = robjects.r('lmer(Reaction ~ Days + (Days | Subject), sleepstudy)')

   `res3` will be a `MER` instance: there is no mapping for the R/S4 class `lmerMod` but there
   is a mapping for its R/S4 parent `merMod`. `res4` will be an `LMER` instance. 
