.. _rinterface-memory:

Memory management and garbage collection
----------------------------------------

The tracking of an R object (:c:type:`SEXP` in R's C-API) 
differs from Python as it does not involve reference counting.
It is using at attribute NAMED (more on this below),
and only considers for collection objects that are not preserved by
being contained in an other R object (for floating object, R's C-API
has 2 functions :c:func:`R_PreserveObject` and :c:func:`R_ReleaseObject` that do little more than placing object is in a container called :c:data:`R_PreciousList`).

Reference counting
^^^^^^^^^^^^^^^^^^

Rpy2 is using its own reference counting system in order to bridge R with
Python and keep as much as possible the pass-by-reference approach familiar
to Python users.

The number of times an R object is used in rpy2, therefore is protected
from garbage collection, is available from Python (obviously read-only):

>>> import rpy2.rinterface as ri
>>> ri.initr()
>>> x = ri.IntSexpVector([1,2,3])
>>> x.__sexp_refcount__
1

That counter will increment each time a new Python reference to it is created.

>>> letters = ri.baseenv['letters']
>>> letters.__sexp_refcount__
1
>>> letters_again = ri.baseenv['letters']
>>> # check that the R ID is the same
>>> letters_again.rid == letters.rid
True
>>> # reference count has increased
>>> letters_again.__sexp_refcount__
2
>>> letters.__sexp_refcount__
2

.. note::

   The attribute `rid` is simply the memory address at which the R-defined
   C-structure containing the R objects is located.

A list of all R IDs protected from garbage collection by rpy2
along with their reference count can be obtained by calling
:func:`rpy2.rinterface.protected_rids`.

We can check that our python object `x` is in indeed listed as protected
from garbage collection (yet it is not bound to any symbol in R - as far as
R is concerned it is like an anonymous variable):

>>> x.rid in (elt[0] for elt in ri.protected_rids())
True

The number of Python/rpy2 objects protecting the R objects from
garbage collection can is also available.

>>> [elt[1] for elt in ri.protected_rids() if elt[0]==x.rid]
[1]

.. note::

   The exact count will depend on what has happened with the current Python
   process, that is whether the R object is already tracked by rpy2 or not.

   Binding the rpy2 object to a new Python symbol will not increase the count
   (because Python knows that the two objects are the same, and R has not been
   involved in that):
   
   >>> y = x
   >>> [elt[1] for elt in ri.protected_rids() if elt[0]==x.rid]
   [1]

   On the other hand, explictly wrapping again the R object through an rpy2
   constructor will increase the count by one:

   >>> z = ri.IntSexpVector(x)
   >>> [elt[1] for elt in ri.protected_rids() if elt[0]==x.rid]
   [2]
   >>> x.rid == z.rid
   True

   In the last case, Python does not know that the 2 objects point to the
   same underlying R object and this mechanism is intended to prevent a
   premature garbage collection of the R object.

   >>> del(x); del(y) # remember that we did `y = x`
   >>> [elt[1] for elt in ri.protected_rids() if elt[0]==z.rid]
   [1]


To achieve this, and keep close to the pass-by-reference approach in Python,
the :c:type:`SexpObject` for a given R object is not part of a Python object
representing it. The Python object only holds a reference to it,
and each time a Python object pointing to a given R object 
(identified by its :c:type:`SEXP`) is created the rpy counter for it is
incremented.

The rpy2 object (proxy for an R object) is implemented as a regular Python
object to which a :c:type:`SexpObject` pointer is appended.

.. code-block:: c

   typedef struct {
       PyObject_HEAD 
       SexpObject *sObj;
   } PySexpObject;

   
The tracking of the capsule itself is what protects the
object from garbage collection on either the R or the Python side.

>>> letters_cstruct = letters.__sexp__
>>> del(letters, letters_again)

The underlying R object is available for collection after the capsule
is deleted (that particular object won't be deleted because R itself tracks it
as part of the base package).

>>> del(letters_cstruct)

Capsules of R objects
^^^^^^^^^^^^^^^^^^^^^

The :c:type:`SexpObject` can be passed around as a (relatively) opaque
C structure, using the attribute :attr:`__sexp__` (a Python `capsule`).

Behind the scene, the capsule is a singleton: given an R object,
it is created with the first Python (rpy2) object wrapping it and
a counter is increased and decreased as other Python objects
expose it as well.

At the C level, the `struct` :c:type:`SexpObject` is defined as:

- a reference count on the Python side

- a possible future reference count on the R side
  (currently unused)
  
- a pointer to the R :c:type:`SEXPREC`

.. code-block:: c
		
   typedef struct {
       Py_ssize_t pycount;
       int rcount;
       SEXP sexp;
   } SexpObject;

The capsule is used to provide a relatively safe composition-like flavor
to the inheritance-based general design of R objects in rpy2, but should
one require access to the underlying R :c:type:`SEXP` object it remains
possible to access it. The following example demonstrates one way to do
it without writing any C code:

.. code-block:: python

   import ctypes

   # Python C API: get the capsule name (of a capsule object)
   pycapsule_getname=ctypes.pythonapi.PyCapsule_GetName
   pycapsule_getname.argtypes = [ctypes.py_object,]
   pycapsule_getname.restype=ctypes.c_char_p
   
   # Python C API: return whether a Python objects is a valid capsule object
   pycapsule_isvalid=ctypes.pythonapi.PyCapsule_IsValid
   pycapsule_isvalid.argtypes=[ctypes.py_object, ctypes.c_char_p]
   pycapsule_isvalid.restype=ctypes.c_bool
   
   # Python C API: return the C pointer
   pycapsule_getpointer=ctypes.pythonapi.PyCapsule_GetPointer
   pycapsule_getpointer.argtypes=[ctypes.py_object, ctypes.c_char_p]
   pycapsule_getpointer.restype=ctypes.c_void_p

   class SexpObject(ctypes.Structure):
       """ C structure SexpObject as defined in the C
           layer of rpy2. """
       _fields_ = [('pycount', ctypes.c_ssize_t),
                   ('rcount', ctypes.c_int),
                   ('sexp', ctypes.c_void_p)]

   # Function to extract the pointer to the underlying R object
   # (*SEXPREC, that is SEXP)
   RPY2_CAPSULENAME=b'rpy2.rinterface._rinterface.SEXPOBJ_C_API'
   def get_sexp(obj):
       assert pycapsule_isvalid(obj, RPY2_CAPSULENAME)
       void_p=pycapsule_getpointer(obj, RPY2_CAPSULENAME)
       return ctypes.cast(void_p, ctypes.POINTER(SexpObject).contents.sexp

.. code-block:: python
		
   from rpy2.rinterface import globalenv
   # Pointer to SEXPREC for the R Global Environment
   sexp=get_sexp(globalenv)
      
Changing the `SEXP` in :c:type:`SexpObject` this way is not advised because
of the risk to confuse the object tracking in rpy2, and ultimately create a segfault.
(I have not thought too long about this. May be the object tracking is more robust
than it think. Just be warned.)
   
   
R's NAMED
^^^^^^^^^

.. warning::

   Starting with version 4.0, R not longer uses `NAMED` to keep track of whether
   an R object can be collected. It is now using a reference-counting system.

Whenever the pass-by-value paradigm is applied strictly,
garbage collection is straightforward as objects only live within
the scope they are declared, but R is using a slight modification
of this in order to minimize memory usage. Each R object has an
attribute :attr:`Sexp.named` attached to it, indicating
the need to copy the object.

>>> import rpy2.rinterface as ri
>>> ri.initr()
0
>>> ri.baseenv['letters'].named
0

Now we assign the vector *letters* in the R base namespace
to a variable *mine* in the R globalenv namespace:

>>> ri.baseenv['assign'](ri.StrSexpVector(("mine", )), ri.baseenv['letters'])
<rpy2.rinterface.SexpVector - Python:0xb77ad280 / R:0xa23c5c0>
>>> tuple(ri.globalenv)
("mine", )
>>> ri.globalenv["mine"].named
2

The *named* is 2 to indicate to :program:`R` that *mine* should be 
copied if a modification of any sort is performed on the object. That copy
will be local to the scope of the modification within R.

