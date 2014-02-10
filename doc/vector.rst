.. module:: rpy2.robjects.vector
   :platform: Unix, Windows
   :synopsis: High-level interface with R

Vectors and arrays
==================

Beside functions and environments, most of the objects
an R user is interacting with are vector-like.
For example, this means that any scalar is in fact a vector
of length one.

The class :class:`Vector` has a constructor:

>>> x = robjects.Vector(3)


.. autoclass:: rpy2.robjects.Vector(o)
   :show-inheritance:
   :members:


Creating vectors
----------------

Creating vectors can be achieved either from R or from Python.

When the vectors are created from R, one should not worry much
as they will be exposed as they should by :mod:`rpy2.robjects`.

When one wants to create a vector from Python, either the 
class :class:`Vector` or the convenience classes
:class:`IntVector`, :class:`FloatVector`, :class:`BoolVector`, 
:class:`StrVector` can be used.

.. autoclass:: rpy2.robjects.vectors.BoolVector(obj)
   :show-inheritance:
   :members:

.. autoclass:: rpy2.robjects.vectors.IntVector(obj)
   :show-inheritance:
   :members:

.. autoclass:: rpy2.robjects.vectors.FloatVector(obj)
   :show-inheritance:
   :members:

.. autoclass:: rpy2.robjects.vectors.StrVector(obj)
   :show-inheritance:
   :members:

.. autoclass:: rpy2.robjects.vectors.ListVector(obj)
   :show-inheritance:
   :members:

Sequences of date or time points can be stored in
:class:`POSIXlt` or :class:`POSIXct` objects. Both can be created
from Python sequences of :class:`time.struct_time` objects or
from R objects.

.. autoclass:: rpy2.robjects.vectors.POSIXlt(obj)
   :show-inheritance:
   :members:

.. autoclass:: rpy2.robjects.vectors.POSIXct(obj)
   :show-inheritance:
   :members:

.. versionadded:: 2.2.0
   Vectors for date or time points


FactorVector
^^^^^^^^^^^^

R's factors are somewhat peculiar: they aim at representing
a memory-efficient vector of labels, and in order to achieve it
are implemented as vectors of integers to which are associated a (presumably
shorter) vector of labels. Each integer represents the position
of the label in the associated vector of labels.

For example, the following vector of labels

+---+---+---+---+---+---+
| a | b | a | b | b | c |
+---+---+---+---+---+---+

will become

+---+---+---+---+---+---+
| 1 | 2 | 1 | 2 | 2 | 3 |
+---+---+---+---+---+---+

and

+---+---+---+
| a | b | c |
+---+---+---+

>>> sv = ro.StrVector('ababbc')
>>> fac = ro.FactorVector(sv)
>>> print(fac)
[1] a b a b b c
Levels: a b c
>>> tuple(fac)
(1, 2, 1, 2, 2, 3)
>>> tuple(fac.levels)
('a', 'b', 'c')

Since a :class:`FactorVector` is an :class:`IntVector` with attached
metadata (the levels), getting items Python-style was not changed from
what happens when gettings items from a :class:`IntVector`.
A consequence to that is that information about the
levels is then lost.

>>> item_i = 0
>>> fac[item_i]
1

Getting the level corresponding to an item requires using the :attr:`levels`,:

>>> fac.levels[fac[item_i] - 1]
'a'

.. warning::

   Do not forget to subtract one to the value in the :class:`FactorVector`.
   Indexing in Python starts at zero while indexing R starts at one,
   and recovering the level for an item requires an adjustment between the two.


When extracting elements from a :class:`FactorVector` a sensible default
might be to use R-style extracting (see :ref:`robjects-extracting`),
as it preserves the integer/string duality.

.. autoclass:: rpy2.robjects.vectors.FactorVector(obj)
   :show-inheritance:
   :members:


.. index::
   pair: Vector;extracting

.. _robjects-extracting:

Extracting items
----------------

Extracting elements of sequence/vector can become a thorny issue
as Python and R differ on a number of points
(index numbers starting at zero / starting at one,
negative index number meaning *index from the end* / *everything except*,
names cannot / can be used for subsettting).

In order to solve this, the Python way and the R way were
made available through two different routes.

Extracting, Python-style
^^^^^^^^^^^^^^^^^^^^^^^^^

The python :meth:`__getitem__` method behaves like a Python user would expect
it for a vector (and indexing starts at zero).

>>> x = robjects.r.seq(1, 5)
>>> tuple(x)
(1, 2, 3, 4, 5)
>>> x.names = robjects.StrVector('abcde')
>>> print(x)
a b c d e 
1 2 3 4 5
>>> x[0]
1
>>> x[4]
5
>>> x[-1]
5

Extracting, R-style
^^^^^^^^^^^^^^^^^^^

Access to R-style extracting/subsetting is granted though the two
delegators *rx* and *rx2*, representing the R functions *[* and *[[*
respectively.

In short, R-style extracting has the following characteristics:

* indexing starts at one

* the argument to subset on can be a vector of 

  - integers (negative integers meaning exlusion of the elements)

  - booleans

  - strings (whenever the vector has *names* for its elements)


>>> print(x.rx(1))
[1] 1
>>> print(x.rx('a'))
a
1

R can extract several elements at once:

>>> i = robjects.IntVector((1, 3))
>>> print(x.rx(i))
[1] 1 3
>>> b = robjects.BoolVector((False, True, False, True, True))
>>> print(x.rx(b))
[1] 2 4 5

When a boolean extract vector is of smaller length than the vector,
is expanded as necessary (this is know in R as the `recycling rule`):
 
>>> print(x.rx(True))
1:5
>>> b = robjects.BoolVector((False, True))
>>> print(x.rx(b))
[1] 2 4

In R, negative indices are understood as element exclusion.

>>> print(x.rx(-1))
2:5
>>> i = robjects.IntVector((-1, -3))
>>> print(x.rx(i))
[1] 2 4 5

That last example could also be written:

>>> i = - robjects.IntVector((1, 3)).ro
>>> print(x.rx(i))
[1] 2 4 5

This extraction system is quite expressive, as it allows a very simple writting of 
very common tasks in data analysis such as reordering and random sampling.

>>> from rpy2.robjects.packages import importr
>>> base = importr('base')
>>> x = robjects.IntVector((5,3,2,1,4))
>>> o_i = base.order(x)
>>> print(x.rx(o_i))
[1] 1 2 3 4 5
>>> rnd_i = base.sample(x)
>>> x_resampled = x.rx(o_i)


R operators are vector operations, with the operator applyied
to each element in the vector. This can be used to build extraction
indexes.

>>> i = x.ro > 3 # extract values > 3
>>> i = (x.ro >= 2 ).ro & (x.ro <= 4) # extract values between 2 and 4

(More on R operators in Section  :ref:`robjects-operationsdelegator`).


R/S also have particularities, in which some see consistency issues.
For example although the indexing starts at 1, indexing on 0
does not return an *index out of bounds* error but a vector
of length 0:

>>> print(x.rx(0))
integer(0)


Assigning items
---------------


Assigning, Python-style
^^^^^^^^^^^^^^^^^^^^^^^

Since vectors are exposed as Python mutable sequences, the assignment works
as for regular Python lists.

>>> x = robjects.IntVector((1,2,3))
>>> print(x)
[1] 1 2 3
>>> x[0] = 9
>>> print(x)
[1] 9 2 3

In R vectors can be *named*, that is elements of the vector have a name.
This is notably the case for R lists. Assigning based on names can be made
easily by using the method :meth:`Vector.index`, as shown below.

>>> x = robjects.ListVector({'a': 1, 'b': 2, 'c': 3})
>>> x[x.names.index('b')] = 9

.. note::

   :meth:`Vector.index` has a complexity linear in the length of the vector's length;
   this should be remembered if performance issues are met.



Assigning, R-style
^^^^^^^^^^^^^^^^^^

Differences between the two languages require few adaptations, and in
appearance complexify a little the task.
Should other Python-based systems for the representation of (mostly numerical)
data structure, such a :mod:`numpy` be preferred, one will be encouraged to expose
our rpy2 R objects through those structures.

The attributes *rx* and *rx2* used previously can again be used:

>>> x = robjects.IntVector(range(1, 4))
>>> print(x)
[1] 1 2 3
>>> x.rx[1] = 9
>>> print(x)
[1] 9 2 3

For the sake of complete compatibility with R, arguments can be named
(and passed as a :class:`dict` or :class:`rpy2.rlike.container.TaggedList`).

>>> x = robjects.ListVector({'a': 1, 'b': 2, 'c': 3})
>>> x.rx2[{'i': x.names.index('b')}] = 9


.. _robjects-missingvalues:

Missing values
--------------

Anyone with experience in the analysis of real data knows that
some of the data might be missing. In S/Splus/R special *NA* values can be used
in a data vector to indicate that fact, and :mod:`rpy2.robjects` makes aliases for
those available as data objects :data:`NA_Logical`, :data:`NA_Real`,
:data:`NA_Integer`, :data:`NA_Character`, :data:`NA_Complex`.

>>> x = robjects.IntVector(range(3))
>>> x[0] = robjects.NA_Integer
>>> print(x)
[1] NA  1  2

The translation of NA types is done at the item level, returning a pointer to
the corresponding NA singleton class.

>>> x[0] is robjects.NA_Integer
True
>>> x[0] == robjects.NA_Integer
True
>>> [y for y in x if y is not robjects.NA_Integer]
[1, 2]

.. note::

   :data:`NA_Logical` is the alias for R's *NA*.

.. note::

   The NA objects are imported from the corresponding
   :mod:`rpy2.rinterface` objects.


.. _robjects-operationsdelegator:

Operators
---------

Mathematical operations on two vectors: the following operations
are performed element-wise in R, recycling the shortest vector if, and
as much as, necessary.

To expose that to Python, a delegating attribute :attr:`ro` is provided
for vector-like objects.

+----------+-----------------+
| Python   |    R            |
+==========+=================+
| ``+``    | ``+``           |
+----------+-----------------+
| ``-``    | ``-``           |
+----------+-----------------+
| ``*``    | ``*``           |
+----------+-----------------+
| ``/``    | ``/``           |
+----------+-----------------+
| ``**``   | ``**`` or ``^`` |
+----------+-----------------+
| ``or``   | ``|``           |
+----------+-----------------+
| ``and``  | ``&``           |
+----------+-----------------+
| ``<``    | ``<``           |
+----------+-----------------+
| ``<=``   | ``<=``          |
+----------+-----------------+
| ``==``   | ``==``          |
+----------+-----------------+
| ``!=``   | ``!=``          |
+----------+-----------------+

>>> x = robjects.r.seq(1, 10)
>>> print(x.ro + 1)
2:11

.. note::
   In Python, using the operator ``+`` on two sequences 
   concatenates them and this behavior has been conserved:

   >>> print(x + 1)
   [1]  1  2  3  4  5  6  7  8  9 10  1

.. note::
   The boolean operator ``not`` cannot be redefined in Python (at least up to
   version 2.5), and its behavior could not be made to mimic R's behavior

.. index::
   single: names; robjects

Names
-----

``R`` vectors can have a name given to all or some of the elements.
The property :attr:`names` can be used to get, or set, those names.

>>> x = robjects.r.seq(1, 5)
>>> x.names = robjects.StrVector('abcde')
>>> x.names[0]
'a'
>>> x.names[0] = 'z'
>>> tuple(x.names)
('z', 'b', 'c', 'd', 'e')


.. index::
   pair: robjects;Environment
   pair: robjects;globalenv

:class:`Array`
---------------

In `R`, arrays are simply vectors with a dimension attribute. That fact
was reflected in the class hierarchy with :class:`robjects.Array` inheriting
from :class:`robjects.Vector`.

.. autoclass:: rpy2.robjects.vectors.Array(obj)
   :show-inheritance:
   :members:



:class:`Matrix`
----------------

A :class:`Matrix` is a special case of :class:`Array`. As with arrays,
one must remember that this is just a vector with dimension attributes
(number of rows, number of columns).

>>> m = robjects.r.matrix(robjects.IntVector(range(10)), nrow=5)
>>> print(m)
     [,1] [,2]
[1,]    0    5
[2,]    1    6
[3,]    2    7
[4,]    3    8
[5,]    4    9

.. note::

   In *R*, matrices are column-major ordered, although the constructor 
   :func:`matrix` accepts a boolean argument *byrow* that, when true, 
   will build the matrix *as if* row-major ordered.

Computing on matrices
^^^^^^^^^^^^^^^^^^^^^

Regular operators work element-wise on the underlying vector.

>>> m = robjects.r.matrix(robjects.IntVector(range(4)), nrow=2)
>>> print(m.ro + 1)
     [,1] [,2]
[1,]    1    3
[2,]    2    4

For more on operators, see :ref:`robjects-operationsdelegator`.

Matrix multiplication is available as :meth:`Matrix.dot`, 
transposition as :meth:`Matrix.transpose`. Common
operations such as cross-product, eigen values computation
, and singular value decomposition are also available through
method with explicit names.

>>> print( m.crossprod(m) )
     [,1] [,2]
[1,]    1    3
[2,]    3   13
>>> print( m.transpose().dot(m) )
     [,1] [,2]
[1,]    1    3
[2,]    3   13


.. autoclass:: rpy2.robjects.vectors.Matrix(obj)
   :show-inheritance:
   :members:



Extracting
^^^^^^^^^^

Extracting can still be performed Python-style or
R-style.

>>> m = ro.r.matrix(ro.IntVector(range(2, 8)), nrow=3)
>>> print(m)
     [,1] [,2]
[1,]    2    5
[2,]    3    6
[3,]    4    7
>>> m[0]
2
>>> m[5]
7
>>> print(m.rx(1))
[1] 2
>>> print(m.rx(6))
[1] 7

Matrixes are two-dimensional arrays, and elements can
be extracted according to two indexes:

>>> print(m.rx(1, 1))
[1] 2
>>> print(m.rx(3, 2))
[1] 7


Extracting a whole row, or column can be achieved by replacing an index number
by `True` or `False`

Extract the first column:

>>> print(m.rx(True, 1))

Extract the second row:

>>> print(m.rx(2, True))



.. _robjects-dataframes:

:class:`DataFrame`
------------------

Data frames are a common way in R to
represent the data to analyze.

A data frame can be thought of as a tabular representation of data,
with one variable per column, and one data point per row. Each column
is an R vector, which implies one type for all elements
in one given column, and which allows for possibly different types across
different columns.

If we consider for example tre data about pharmacokinetics of theophylline in
different subjects, the data table could look like this:

======= ====== ==== ==== ====
Subject Weight Dose Time conc
======= ====== ==== ==== ====
 1       79.6  4.02 0.00 0.74
 1       79.6  4.02 0.25 2.84
 1       79.6  4.02 0.57 6.57
 2       72.4  4.40 7.03 5.40
 ...     ...   ...  ...  ...
======= ====== ==== ==== ====

Such data representation shares similarities with a table in
a relational database: the structure between the variables, or columns,
is given by other column. In the example above, the grouping of
measures by subject is given by the column *Subject*.


In :mod:`rpy2.robjects`, 
:class:`DataFrame` represents the `R` class `data.frame`.

Creating objects
^^^^^^^^^^^^^^^^

Creating a :class:`DataFrame` can be done by:

* Using the constructor for the class

* Create the data.frame through R

* Read data from a file using the instance method :meth:`from_csvfile`

The :class:`DataFrame` constructor accepts either an
:class:`rinterface.SexpVector` 
(with :attr:`typeof` equal to *VECSXP*, that is, an R `list`)
or any Python object implementing the method :meth:`iteritems`
(for example :class:`dict` or :class:`rpy2.rlike.container.OrdDict`).

Empty `data.frame`:

>>> dataf = robjects.DataFrame({})

`data.frame` with 2 two columns (not that the order of
the columns in the resulting :class:`DataFrame` can be different
from the order in which they are declared):

>>> d = {'a': robjects.IntVector((1,2,3)), 'b': robjects.IntVector((4,5,6))}
>>> dataf = robject.DataFrame(d)

To create a :class:`DataFrame` and be certain of the clumn order order,
an ordered dictionary can be used:

>>> import rpy2.rlike.container as rlc
>>> od = rlc.OrdDict([('value', robjects.IntVector((1,2,3))),
                      ('letter', robjects.StrVector(('x', 'y', 'z')))])
>>> dataf = robjects.DataFrame(od)
>>> print(dataf.colnames)
[1] "letter" "value"

Creating the data.frame in R can otherwise be achieved in numerous ways,
as many R functions do return a `data.frame`, such as the
function `data.frame()`.

.. note::

   When creating a :class:`DataFrame`, vectors of strings are automatically
   converted by R into instances of class :class:`Factor`. This behavior
   can be prevented by wrapping the call into the R base function I.
   
   .. code-block:: python

      from rpy2.robjects.vectors import DataFrame, StrVector
      from rpy2.robjects.packages import importr
      base = importr('base')
      dataf = DataFrame({'string': base.I(StrVector('abbab')),
                         'factor': StrVector('abbab')})

   Here the :class:`DataFrame` `dataf` now has two columns, one as 
   a :class:`Factor`, the other one as a :class:`StrVector`
 
   >>> dataf.rx2('string')
   <StrVector - Python:0x95fe5ec / R:0x9646ea0>
   >>> dataf.rx2('factor')
   <FactorVector - Python:0x95fe86c / R:0x9028138>



Extracting elements
^^^^^^^^^^^^^^^^^^^

Here again, Python's :meth:`__getitem__` will work
as a Python programmer will expect it to:

>>> len(dataf)
2
>>> dataf[0]
<Vector - Python:0x8a58c2c / R:0x8e7dd08>

The :class:`DataFrame` is composed of columns,
with each column being possibly of a different type:

>>> [column.rclass[0] for column in dataf]
['factor', 'integer']

Using R-style access to elements is a little richer,
with the *rx2* accessor taking more importance than earlier.

Like with Python's :meth:`__getitem__` above,
extracting on one index selects columns:

>>> dataf.rx(1)
<DataFrame - Python:0x8a584ac / R:0x95a6fb8>
>>> print(dataf.rx(1))
  letter
1      x
2      y
3      z

Note that the result is itself
of class :class:`DataFrame`. To get the column as
a vector, use *rx2*:

>>> dataf.rx2(1)
<Vector - Python:0x8a4bfcc / R:0x8e7dd08>
>>> print(dataf.rx2(1))
[1] x y z
Levels: x y z


Since data frames are table-like structure, they
can be thought of as two-dimensional arrays and
can therefore be extracted on two indices.

>>> subdataf = dataf.rx(1, True)
>>> print(subdataf)
  letter value
1      x     1
>>> rows_i <- robjects.IntVector((1,3))
>>> subdataf = dataf.rx(rows_i, True)
>>> print(subdataf)
  letter value
1      x     1
3      z     3

That last example is extremely common in R. A vector of indices,
here *rows_i*, is used to take a subset of the :class:`DataFrame`.




Python docstrings
^^^^^^^^^^^^^^^^^

.. autoclass:: rpy2.robjects.vectors.DataFrame(tlist)
   :show-inheritance:
   :members:
