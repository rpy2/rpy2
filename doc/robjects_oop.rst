Working with R's OOPs
=====================

Object-Oriented Programming can be achieved in R, but in more than
one way. Beside the *official* S3 and S4 systems, there is a rich
ecosystem of alternative implementations of objects, like aroma, or proto.

S3 objects
----------

S3 objects are default R objects (i.e., not S4 instances) for which
an attribute "class" has been added.

>>> x = robjects.IntVector((1, 3))
>>> tuple(x.rclass)
('integer',)

Making the object x an instance of a class *pair*, itself inheriting from
*integer* is only a matter of setting the attribute:

>>> x.rclass = robjects.StrVector(("pair", "integer"))
>>> tuple(x.rclass)
('pair', 'integer')

Methods for *S3* classes are simply R functions with a name such as name.<class_name>,
the dispatch being made at run-time from the first argument in the function call.

For example, the function *plot.lm* plots objects of class *lm*. The call
*plot(something)* makes R extract the class name of the object something, and see
if a function *plot.<class_of_something>* is in the search path.

.. note::

   This rule is not strict as there can exist functions with a *dot* in their name
   and the part after the dot not correspond to an S3 class name. 

.. module:: rpy2.robjects.methods
   :synopsis: S4 OOP in R

S4 objects
----------

S4 objects are a little more formal regarding their class definition, and all
instances belong to the low-level R type SEXPS4.

The definition of methods for a class can happen anytime after the class has
been defined (a practice something referred to as *monkey patching*
or *duck punching* in the Python world).

There are obviously many ways to try having a mapping between R classes and Python
classes, and the one proposed here is to make Python classes that inherit
:class:`rpy2.rinterface.methods.RS4`.

Before looking at automated ways to reflect R classes as Python classes, we look
at how a class definition in Python can be made to reflect an R S4 class.
We take the R class `lmList` in the package `lme4` and show how to write
a Python wrapper for it.

Manual R-in-Python class definition
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. note::

   The R package `lme4` is not distributed with R, and will have to be installed
   for this example to work.

First, a bit of boilerplate code is needed. We
import the higher-level interface and the function 
:func:`rpy2.robjects.packages.importr`. The R class we want to represent
is defined in the 
:mod:`rpy2` modules and utilities. 

.. literalinclude:: _static/demos/s4classes.py
   :start-after: #-- setup-begin
   :end-before:  #-- setup-end

Once done, the Python class definition can be written.
In the first part of that code, we choose a static mapping of the
R-defined methods. The advantage for doing so is a bit of speed
(as the S4 dispatch mechanism has a cost), and the disadvantage
is that a modification of the method at the R level would require
a refresh of the mappings concerned. The second part of the code
is a wrapper to those mappings, where Python-to-R operations prior
to calling the R method can be performed.
In the last part of the class definition, a *static method* is defined.
This is one way to have polymorphic constructors implemented.

.. literalinclude:: _static/demos/s4classes.py
   :start-after: #-- LmList-begin
   :end-before:  #-- LmList-end

Creating a instance of :class:`LmList` can now be achieved by specifying
a model as a :class:`Formula` and a dataset.

.. literalinclude:: _static/demos/s4classes.py
   :start-after: #-- buildLmList-begin
   :end-before:  #-- buildLmList-end

A drawback of the approach above is that the R "call" is stored,
and as we are passing the :class:`DataFrame` *sleepstudy* 
(and as it is believed to to be an anonymous structure by R) the call
is verbose: it comprises the explicit structure of the data frame
(try to print *lml1*). This becomes hardly acceptable as datasets grow bigger.
An alternative to that is to store the columns of the data frame into
the environment for the :class:`Formula`, as shown below:

.. literalinclude:: _static/demos/s4classes.py
   :start-after: #-- buildLmListBetterCall-begin
   :end-before:  #-- buildLmListBetterCall-end

.. autoclass:: rpy2.robjects.methods.RS4(sexp)
   :show-inheritance:
   :members:

Automated R-in-Python class definitions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The S4 system allows polymorphic definitions of methods, that is,
there can be several methods with the same name but different number and types of arguments.
(This is like Clojure's multimethods). Mapping R methods to Python methods
automatically and reliably requires a bit of work, and we chose to concatenate
the method name with the type of the parameters in the signature.

Using the automatic mapping is very simple. One only needs to declare
a Python class with the following attributes:

+----------------------+-----------+----------------------------+
| __rname__            | mandatory |  the name of the R class   |
+----------------------+-----------+----------------------------+
| __rpackagename__     | optional  | the R package in which the |
|                      |           | class is declared          |
+----------------------+-----------+----------------------------+
| __attr_translation__ | optional  | :class:`dict` to translate |
+----------------------+-----------+----------------------------+
| __meth_translation__ | optional  | :class:`dict` to translate |
+----------------------+-----------+----------------------------+

Example:

.. code-block:: python

   from rpy2.robjects.packages import importr
   stats4 = importr('stats4')
   from rpy2.robjects.methods import RS4, RS4Auto_Type
   
   class MLE(RS4):
     __metaclass__ = RS4Auto_Type
     __rname__ = 'mle'
     __rpackagename__ = 'stats4'

The class `MLE` just defined has all attributes and methods needed
to represent all slots (`attributes` in the S4 nomenclature)
and methods defined for the class when the class is declared
(remember that class methods can be declared afterwards, or even in a different
R package).

.. autoclass:: rpy2.robjects.methods.RS4Auto_Type(sexp)
   :show-inheritance:
   :members:

Automated mapping of user-defined classes
-----------------------------------------

Once a Python class mirroring an R classis is defined, the mapping can be made
automatic by adding new rules to the conversion system
(see Section :ref:`robjects-conversion`).

