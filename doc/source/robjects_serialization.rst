
Object serialization
====================

The python pickling system can be used to serialize objects to disk,
and restore them from their serialized form.

.. code-block:: python

   import pickle
   import rpy2.robjects as ro

   x = ro.StrVector(('a', 'b', 'c'))
   base_help.fetch('sum')
   f = file('/tmp/foo.pso', 'w')
   pickle.dump(x, f)
   f.close()


   f = file('/tmp/foo.pso', 'r')
   x_again = pickle.load(f)
   f.close()


.. warning::

   Currently loading an object from a serialized form restores the object in
   its low-level form (as in :mod:`rpy2.rinterface`). Higher-level objects
   can be restored by calling the higher-level casting function
   :func:`rpy2.robjects.conversion.ri2py` (see :ref:`robjects-conversion`).
