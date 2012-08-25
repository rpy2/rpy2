
.. index::
   pair: robjects; Function
   pair: robjects; function

.. _robjects-functions:

Functions
=========

R functions are callable objects, and can be called almost like any regular
Python function:

>>> plot = robjects.r.plot
>>> rnorm = robjects.r.rnorm
>>> plot(rnorm(100), ylab="random")

This is all looking fine and simple until R arguments with names 
such as `na.rm` are encountered. By default, this is addressed by
having a translation of '.' (dot) in the R argument name into a '_' in the Python
argument name.

Let's take an example in R:

.. code-block:: r

   rank(0, na.last = TRUE)

In Python one can write:

.. code-block:: python

   from rpy2.robjects.packages import importr
   base = importr('base')

   base.rank(0, na_last = True)

.. note::

   In this example, the object `base.rank` is an instance of
   :class:`functions.SignatureTranslatedFunction`,
   a child class of :class:`functions.Function`, and the translation of 
   the argument names is made during the creation of the instance.
   Making the translation during the creation obviously 
   saves the need to perform translation operations on parameter names,
   such as replacing `.` with `_`,
   at each function call, and allows `rpy2` to perform sanity checks
   regarding possible ambiguous translations; the cost of doing it is
   acceptable cost since this is only performed when the instance is created.

   If no translation is desired, the class :class:`functions.Function` 
   can be used. With
   that class, using the special Python syntax `**kwargs` is one way to specify
   named arguments to R functions that contain a dot '.'

   One will note that the translation is done by inspecting
   the signature of the R function, and that not much can be guessed from the
   R ellipsis '...' whenever present. Arguments falling in the '...' will need
   to have their R names passed to the constructor for
   :class:`functions.SignatureTranslatedFunction` as show in the example below:

   >>> graphics = importr('graphics')
   >>> graphics.par(cex_axis = 0.5)
   Warning message:
   In function (..., no.readonly = FALSE)  :
   "cex_axis" is not a graphical parameter
   <Vector - Python:0xa1688cc / R:0xab763b0>
   >>> graphics.par(**{'cex.axis': 0.5})
   <Vector - Python:0xae8fbec / R:0xaafb850>

   There exists a way to specify manually a argument mapping:

   .. code-block:: python

      from rpy2.robjects.functions import SignatureTranslatedFunction
      from rpy2.robjects.packages import importr
      graphics = importr('graphics')
      graphics.par = SignatureTranslatedFunction(graphics.par,
                                                 init_prm_translate = {'cex_axis': 'cex.axis'})

   >>> graphics.par(cex_axis = 0.5)
   <Vector - Python:0xa2cc90c / R:0xa5f7fd8>

   Translating blindly each '.' in argument names into '_' currently appears
   to be a risky
   practice, and is left to one to decide for his own code. (Bad) example:
 
   .. code-block:: python

      def iamfeelinglucky(**kwargs):
          res = {}
          for k, v in kwargs.iteritems:
              res[k.replace('_', '.')] = v
          return res

      graphics.par(**(iamfeelinglucky(cex_axis = 0.5)))

    
   
Things are also not always that simple, as the use of a dictionary does
not ensure that the order in which the arguments are passed is conserved.

R is capable of introspection, and can return the arguments accepted
by a function through the function `formals()`, modelled as a method of
:class:`functions.Function`.

>>> from rpy2.robjects.packages import importr
>>> stats = importr('stats')
>>> rnorm = stats.rnorm
>>> rnorm.formals()
<Vector - Python:0x8790bcc / R:0x93db250>
>>> tuple(rnorm.formals().names)
('n', 'mean', 'sd')


.. warning::

   Here again there is a twist coming from R, and some functions are "special".
   rpy2 is exposing as :class:`rpy2.rinterface.SexpClosure`  R objects that 
   can be either CLOSXP, BUILTINSXP, or SPECIALSXP. However, only CLOSXP objects
   will return non-null `formals`.


The R functions as defined in :mod:`rpy2.robjects` inherit from the class
:class:`rpy2.rinterface.SexpClosure`, and further documentation
on the behavior of function can be found in Section :ref:`rinterface-functions`.

.. autoclass:: rpy2.robjects.functions.Function(*args, **kwargs)
   :show-inheritance:
   :members:

.. autoclass:: rpy2.robjects.functions.SignatureTranslatedFunction(*args, **kwargs)
   :show-inheritance:
   :members:
