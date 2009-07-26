.. _misc-performances:

************
Performances
************

As a simple benchmark, we took a function that would sum
up all elements in a numerical vector.

pure R:

.. code-block:: r

   function(x) {
     total <- 0
     for (elt in x) {
       total <- total + elt
     }
     return(total)
   }

pure Python:

.. code-block:: python

   def py_sum(x):
       total = 0
       for elt in x:
           total += elt
       return total


We ran this function over different types of sequences (same length, 
same values)

.. code-block:: python

   n = 20000
   x_list = [random.random() for i in xrange(n)]

   import array
   x_array = array.array('f', x_list)

   import numpy
   x_numpy = numpy.array(x_list, 'f')

   import rpy2.robjects as ro
   x_floatvector = ro.FloatVector(x_list)
   x_sexpvector = ro.rinterface.SexpVector(x_floatvector)

All results are made relative to the implementation in pure R,
with the column speedup indicating how many times faster the
code runs.

=============== ========================================== ==========
Function        Sequence                                    Speedup
=============== ========================================== ==========
pure R                                                      1
pure python     :class:`rpy2.rinterface.SexpVector`         *6.8*
pure python     :class:`rpy2.robjects.vectors.FloatVector`  0.6
pure python     :class:`list`                               9.1
pure python     :class:`array.array`                        8.8
pure python     :class:`numpy.array`                        1.2
=============== ========================================== ==========

Iterating through a :class:`list` is likely the fastest, explaining
why implementation of the sum in pure Python is the fastest.
Note that the iterating sum is 9 times faster in Python than in R.

The object one iterates through matters much for the speed, and
the poorest performer is :class:`rpy2.robjects.vectors.FloatVector`,
being almost twice slower than R. This is expected since the iteration
relies on R-level mechanisms to which a penalty for using a higher-level
interface must be added.
On the other hand, using a :class:`rpy2.rinterface.SexpVector` provides
an almost 7x speedup, making the use of R through rpy2 faster that using
R from R. This was again expected, as the lower-level interface is
closer to the C API for R.

More of a surprise, iterating through a :class:`numpy.array` is only
slightly faster than pure R.


Using the popular bytecode optimizer *psyco*, we run again our benchmark
function.


psyco:

.. code-block:: python

   import psyco

   psy_sum = psyco.proxy(py_sum)




=============== ========================================== ==========
Function        Sequence                                    Speedup
=============== ========================================== ==========
psyco           :class:`rpy2.rinterface.SexpVector`         *14.4*
psyco           :class:`rpy2.robjects.vectors.FloatVector`  0.6
psyco           :class:`list`                               27.1
psyco           :class:`array.array`                        19.4
psyco           :class:`numpy.array`                        1.5
=============== ========================================== ==========

When using psyco, we can achieve a 14x speed when looping 
over an *R vector* (the vector is in the R memory space) and summing
its elements from rpy2,
compared to doing the same operation in pure R.



Finally, and to put the earlier benchmarks in perspective, it is
fair to note that python and R have a builtin function *sum*,
calling C-compiled code, and to compare their performances.

=============== ========================================== ==========
Function        Sequence                                    Speedup
=============== ========================================== ==========
builtin python  :class:`rpy2.rinterface.SexpVector`         14.9
builtin python  :class:`rpy2.robjects.vectors.FloatVector`  0.6
builtin python  :class:`list`                               32.7
builtin python  :class:`array.array`                        26.1
builtin python  :class:`numpy.array`                        1.3
builtin R                                                   133.2
numpy.array.sum :class:`numpy.array`                        *272.2*
=============== ========================================== ==========

The builtin python implementation on list is only twice faster
than a pure python implementation on an :class:`rpy2.rinterface.SexpVector`,
accelerated using *psyco*.

:class:`numpy.array.sum` is about twice faster than its R conterpart,
although it is important to remember that the R version handles missing
values.