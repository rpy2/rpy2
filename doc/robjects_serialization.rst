
Object serialization
====================

The R objects in rpy2 are implementing the pickle protocol in Python,
giving access to Python's pickling (serialize objects to disk,
and restore them from their serialized form).

.. code-block:: python

   import pickle
   import rpy2.robjects as ro

   x = ro.StrVector(('a', 'b', 'c'))
   
   x_serialized = pickle.dumps(x, f)

   x_again = pickle.loads(x_serialized)


This is also giving access to Python code using the pickling system
communicate objects across networks or processes such as
:mod:`multiprocessing` and :mod:`pyspark`.
