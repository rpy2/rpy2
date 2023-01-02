
.. index::
   pair: robjects; Function
   pair: robjects; function

.. _robjects-functions:

Functions
=========

.. note::

   This section is about calling R functions from Python.
   To make Python functions
   callable by R, see the low-level function :func:`rpy2.rinterface.rternalize`.

R functions exposed by :mod:`rpy2`'s high-level interface can be used:

- like any regular Python function as they are callable objects
  (see Section :ref:`robjects-functions-callable`)
- through their method :meth:`rcall` (see Section :ref:`robjects-functions-rcall`)


.. _robjects-functions-callable:

Callable
--------

.. code-block:: python
		
   from rpy2.robjects.packages import importr
   base = importr('base')
   stats = importr('stats')
   graphics = importr('graphics')
   
   plot = graphics.plot
   rnorm = stats.rnorm
   plot(rnorm(100), ylab="random")

This is all looking fine and simple until R arguments with names 
such as `na.rm` are encountered. By default, this is addressed by
having a translation of '.' (dot) in the R argument name into a
'_' in the Python
argument name.

Let's take an example in R:

.. code-block:: r

   rank(0, na.last = TRUE)
   # or without the implicit namespace:
   base::(0, na.last = TRUE)

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
   such as replacing `'.'` with `'_'`,
   at each function call, and allows `rpy2` to perform sanity checks
   regarding possible ambiguous translations (`R` functions, even in
   the base libraries, happen to sometimes have both argument names
   `foo.bar` and `foo_bar` in the signature of the same function).
   The cost of performing the mapping is amortized when a function
   is called repeatedly since this is only performed when the instance
   is created.

   If no translation is desired, the class :class:`functions.Function` 
   can be used. With
   that class, using the special Python syntax `**kwargs` is one way to specify
   named arguments to R functions that contain a dot `'.'`

   One will note that the translation is done by inspecting
   the signature of the R function, and that not much can be guessed from the
   R ellipsis `'...'` whenever present. Arguments falling in the `'...'`
   will need
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

   There exists a way to specify manually an argument mapping:

   .. code-block:: python

      from rpy2.robjects.functions import SignatureTranslatedFunction
      STM = SignatureTranslatedFunction
      from rpy2.robjects.packages import importr
      graphics = importr('graphics')
      graphics.par = STM(graphics.par,
                         init_prm_translate = {'cex_axis': 'cex.axis'})

   >>> graphics.par(cex_axis = 0.5)
   <Vector - Python:0xa2cc90c / R:0xa5f7fd8>

   Translating blindly each `'.'` in argument names into `'_'`
   currently appearsto be a risky
   practice, and is left to one to decide for his/her own code.
   The code example is a demonstration of how to do, not a recommendation
   to do it:
 
   .. code-block:: python

      def iamfeelinglucky(func):
          def f(*args, **kwargs):
              d = {}
              for k, v in kwargs.items():
                  d[k.replace('_', '.')] = v
              return func(**d)
          return f

      lucky_par = iamfeelinglucky(graphics.par)
      lucky_path(cex_axis = 0.5)
   
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


.. _robjects-functions-rcall:

:meth:`rcall`
-------------

The method :meth:`Function.rcall` is an alternative way to call an
underlying R function. When using R environment
in which the function should be evaluated must be specified.

We use again the example with `plot()`:

.. code-block:: python
		
   from rpy2.robjects.packages import importr
   base = importr('base')
   stats = importr('stats')
   graphics = importr('graphics')
   
   plot = graphics.plot
   rnorm = stats.rnorm

   # import R's "GlobalEnv" to evaluate the function 
   from rpy2.robjects import globalenv

   # build a tuple of 2-tuple as arguments
   args = (('x', rnorm(100)),)

   # run the function in globalenv
   plot.rcall(args, globalenv)

In the example above the label for y-axis is inferred from the call (in R,
using the function `deparse()`) and this is producing rather undesirably
long labels. This is the case because the vector :py:obj:`x` is an anonymous
object as far a `R` is concerned: while it has a symbol for Python (`"x"`),
it does not have any for `R`.

The method :meth:`rcall` can help overcome this by letting one use
an environment in which the R objects can be bound to a symbol (a name).
While :py:data:`globalenv` can be used, a dedicated environment can lead
to a better compartmentalization of code.

The call above can then become:
   
.. code-block:: python

   from rpy2.robjects import Environment
   
   # Create an R environment
   env = Environment()
   
   # Bind in R the R vector to the symbol "x" and
   # in that environment
   env['x'] = rnorm(100)
   
   # Build a tuple of pairs (<argument name>, <argument>).
   # Note that the argument is a symbol. R will resolve what
   # object is associated to that symbol when the function
   # is executed.
   args = (('x', base.as_symbol('x')),)
   
   # plot
   plot.rcall(args, env)


Docstrings
----------
   
The R functions as defined in :mod:`rpy2.robjects` inherit from the class
:class:`rpy2.rinterface.SexpClosure`, and further documentation
on the behavior of function can be found in Section :ref:`rinterface-functions`.

.. autoclass:: rpy2.robjects.functions.Function(*args, **kwargs)
   :show-inheritance:
   :members:

.. autoclass:: rpy2.robjects.functions.SignatureTranslatedFunction(*args, **kwargs)
   :show-inheritance:
   :members:


Automagic Python functions
--------------------------

Genuine Python functions can also be dynamically created from R functions, complete
with matching signatures.

.. code-block:: python

   r_func_code = """
   function(x, y=FALSE, z="abc") {
     TRUE
   }
   """
   r_func = robjects.r(r_func_code)

   py_func = robjects.functions.wrap_r_function(r_func, 'py_func')

The resulting object :func:`py_func` is a Python function of signature
`(x, y=False, z='abc')`.
