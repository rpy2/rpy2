.. module:: rpy2.robjects.conversion
   :synopsis: Converting rpy2 proxies for R objects into Python objects.

.. _robjects-conversion:

Mapping rpy2 objects to arbitrary python objects
================================================


Protocols
---------

The package has a low level and a high level interface to R. The low level is
closer to R's C API, while the high level is meant to provide more convenience
even if at the cost of performances. The low level (:mod:`rpy2.rinterface`)
is not devoid of any convenience. A minimal set of Pythonic characteristics are
present, allowing rpy2 objects to behave like Python objects of similar nature
and non-rpy2 objects be sometimes usable with R functions when there is
no ambiguity about what conversion between the two systems should be.

For example, R vectors (rank-one arrays) are wrapped to rpy2 classes
implementing the methods :meth:`__len_`, :meth:`__getitem__`, :meth:`__setitem__`
as defined in the sequence
protocol in Python. Python functions working with sequences can then be passed such R
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
:mod:`numpy` functions without the need for data copying or conversion.

.. note::

   Before the move to :mod:`cffi` Python's buffer protocol was also implemented
   but the Python does not allow classes to define it outside of the Python C-API,
   and `cffi` does not allow the use of the Python's C-API.

   Some rpy2 vectors will have a method :meth:`memoryview` that will return
   views that implement the buffer protocol.

R functions are mapped to Python objects that implement :meth:`__call__`. They
can be called just as if they were functions.

R environments are mapped to Python objects that implement :meth:`__len__`,
:meth:`__getitem__`, :meth:`__setitem__` in the mapping protocol so elements
can be accessed similarly to in a Python :class:`dict`.

.. warning::

   While it is technically possible to modify the way C-level R objects
   are shown to Python users through the `rinterface` level, it is not
   recommended. The `rinterface` level is quite close to R's C API and modifying it may quickly
   result in segfaults.

   On the other hand, the robjects-level is designed to facilitate the customization
   of object conversions between Python and R.


Conversion
----------

The high level interface between Python in :mod:`rpy2` uses a conversion system
each time an R object is represented in Python, and each time a Python objects
is passed to R (for example as a parameter to an R function). Those are the
conversion rules you'll mostly experience when using the API in :mod:`rpy2.robjects`
or in the "R magic" used from `ipython` or `jupyter`.

.. note::

   The set of active conversion rules can be customized, including within
   a context (see `Local conversion rules`_). Functions
   in the :mod:`rpy2.robjects` will use the active rules, but if
   wanting the object with currently cactive rules :func:`rpy2.robjects.conversion.get_conversion`
   must be used to fetch them.


This system is designed to manage the conversion between the low level (`rinterface`-level)
interface and an arbitrary Python-level representation those objects.
`py2rpy` will indicate a conversion from Python-level to `rinterface`-level,
and `rpy2py` from `rinterface`-level to Python-level.

If one wanted to turn all Python :class:`tuple` objects
into R `character` vectors (1D arrays of strings) before passing them to R the custom
conversion function would make an `rinterface`-level R objects from the Python object.
An implementation for this `py2rpy` function would look like:
 
.. code-block:: python

   from rpy2.rinterface import StrSexpVector

   
   def tuple_str(tpl):
       res = StrSexpVector(tpl)
       return res

The conversion system is an `robjects`-level feature, and by default the Python-level
representations are just high-level (`robjects`-level) representation. However, the package contains
optional conversion rules in modules :mod:`rpy2.robjects.numpy2ri` and
:mod:`rpy2.robjects.pandas2ri` to convert from and to :mod:`numpy` and :mod:`pandas` objects respectively.

.. note::

   Sections :ref:`robjects-numpy` and :ref:`robjects-pandas` contain information about
   working with rpy2 and :mod:`numpy` or :mod:`pandas` objects.


Converter objects
^^^^^^^^^^^^^^^^^

:class:`rpy2.robjects.conversion.Converter` objects are designed
to keep sets of conversion rules together. There can be as many instances
of that class as desired, but the one called `converter` in
:mod:`rpy2.robjects.conversion` is the one used whenever conversion is needed.

The :class:`Converter` has 2 attributes `rpy2py` and `py2rpy` to resolve
the conversion from R (`rinterface-level`) to an arbitrary Python representation,
and from an arbitrary Python representation to a suitable `rinterface` level.
Each of those is a single dispatch as implemented in
:meth:`functools.singledispatch`. This means that a conversion function,
such as the example function `tuple_str` above, just has to be associated with
the class of the object to convert from. In our example, the Python class is :class:`tuple`.

Our conversion function defined above can be registered in a converter as follows:

.. code-block:: python
   
   from rpy2.robjects.conversion import Converter
   seq_converter = Converter('sequence converter')
   seq_converter.py2rpy.register(tuple, tuple_str)

Alternatively, the registration can be done with a decorator when the function is declared:

.. code-block:: python

   my_converter = rpy2.robjects.conversion.Converter()

   @my_converter.py2rpy(tuple)
   def tuple_str(tpl):
       res = StrSexpVector(tpl)
       return res

The class :class:`rpy2.robjects.conversion.Converter` can group several conversion rules
into one object. This helps will defining sets of coherent conversion rules, or
conversion domains. :mod:`rpy2.robjects.numpy2ri.converter` and :mod:`rpy2.rojects.pandas2ri.converter`
are examples of such converters.

Sets of conversion rules can be layered on the top of one another
to create sets of combined conversion rules. To help with writing concise and
clear code, :class:`Converter` objects can be added. For example, creating a
converter that adds the rule above to the default conversion rules in rpy2
will look like:

.. code-block:: python
		
   from rpy2.robjects import default_converter
   conversion_rules = default_converter + seq_converter

While a dispatch solely based on Python classes will work very well in the
direction "Python to `rpy2.rinterface`" it will quickly show limits in the direction
"`rpy2.rinterface` to Python", especially when independently-developed conversions
must be  combined.

The issue with converting from `rpy2.rinterface` to Python is not working too well
because `rpy2.rinterface` mirrors the type of R objects at the C-level (as
defined in R's C-API), but class definitions in R often sit outside
of structure types found at the C level. They are just a mere attribute of the R object
that contains a list class names. For example, an R `data.frame` is a `VECSXP` at
C-level (that is an R `list`), but it has an attribute `"class"` that contains `"data.frame"`.
   
.. note::

   Nothing would prevent someone to set the `"class"` attribute to `"data.frame"` to an R
   object of different type at C-level. For example, it is perfectly possible to write
   the following in R, and create an invalid data frame:
   
   .. code-block:: r
		   
      > x <- c(1, 2, 3)
      > str(x)
      int [1:3] 1 2 3
      > class(x) <- "data.frame"
      > str(x)
      'data.frame':	0 obs. of  3 variables:
       'data.frame' int  character(0) character(0) character(0)
      Warning message:
        In format.data.frame(x, trim = TRUE, drop0trailing = TRUE, ...) :
        corrupt data frame: columns will be truncated or padded with NAs
 
To allow a dispatch based name-specified classes in R, the rpy2 conversion system
uses a secondary mechanism (the primary mechanism is the single dispatch-based one
presented above).

Instances of :class:`rpy2.robjects.conversion.NameClassMap` can map and R class name to
a Python class. Remember that this mapping only happen within the context of an :mod:`rpy2.rinterface`
class though. The attribute :attr:`rpy2.robjects.conversion.Converter._rpy2py_nc_name` is
a :class:`dict` where keys are :mod:`rpy2.rinterface` classes to wrap C-level R objects, and
values are instances of :class:`rpy2.robjects.conversion.NameClassMap`.

For example, a conversion rule for R objects of class "lm" that are R lists at
the C level (this is a real exemple - R's linear model fit objects are just that)
can be added to a converter with:

.. code-block:: python

   class Lm(rinterface.ListSexpVector):
       # implement attributes, properties, methods to make the handling of
       # the R object more convenient on the Python side
       pass

   clsmap = myconverter._rpy2py_nc_name[rinterface.ListSexpVector]
   clsmap.update({'lm': Lm})


.. _Local conversion rules:

Local conversion rules
^^^^^^^^^^^^^^^^^^^^^^

The conversion rules can be customized globally (See section `Customizing the conversion`)
or locally in a Python `with` block.

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
   with conversion_rules.context():
       res = base.paste(x, collapse="-")

.. note::

   A local conversion rule can also ensure that code is robust against arbitrary changes
   in the conversion system made by the caller.

   For example, to ensure that a function always uses rpy2's default conversion,
   irrespective of what are the conversion rules defined by the caller of the code:

   .. code-block:: python

      from rpy2.robjects import default_converter

      def my_function(obj):
          with default_converter.context():
              # Block of code mixing Python code and calls to R functions
	      # interacting with the objects returned by R in the Python code.
	      # Within this block the conversion rules are the ones of
	      # `default_converter`.
	      pass

   Code in the :mod:`rpy2.robjects` will use whatever the active conversion rules are, but
   there are situations where the set of active conversion rules must be accessed. Whenever
   the case the conversion rules from the context manager can be named.
	  
   .. code-block:: python

      from rpy2.robjects import default_converter
      from rpy2.robjects.conversion import get_conversion

      def my_function(obj):
          with default_converter.context() as local_converter:
	      # `local_converter` is a rpy2.robjects.conversion.Converter
	      # object.
	      pass	  

    .. note::

       The converter returned by :meth:`rpy2.robjects.conversion.Converter.context` is
       a copy of the rules for the context.

       ```python
        with default_converter.context() as local_converter:
	    # Conversion objects are not the same.
	    assert local_converter != default_converter
	    assert cv.py2rpy.registry != default_converter.py2rpy
	    assert cv.rpy2py.registry != default_converter.rpy2py
	    # The convertion rules are identical though.
	    assert dict(cv.py2rpy.registry) == dict(default_converter.py2rpy.registry)
	    assert dict(cv.rpy2py.registry) == dict(default_converter.rpy2py.registry)


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
