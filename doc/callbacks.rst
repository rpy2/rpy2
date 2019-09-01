.. _rinterface-callbacks:

*********
Callbacks
*********

The R C-API allows front-end developpers to customize R's interactive behavior
to their needs using callbacks, and :mod:`rpy2` is making those callbacks
accessible with the ability to implement them in pure Python. In other words,
:mod:`rpy2` makes it possible to implement a completely an R front-end such
as RStudio.

.. _rinterface-callbacks_consoleio:

Console I/O
===========

During an interactive session, much of the communication between R and the
user happen through the console. How the console reads input and writes output,
can be defined through callback functions.

Read console
------------

The function "read console" is called whenever console input is expected.


The default callback for inputing data is
:func:`rpy2.rinterface_lib.callbacks.consoleread`

.. autofunction:: rpy2.rinterface_lib.callbacks.consoleread(prompt)

Any Python function with the same signature can be used instead. For example:

.. code-block:: python

   def  my_consoleread(prompt: str) -> str:
       custom_prompt = f'R is asking this: {promp}'
       return input(custom_prompt)
 
   rpy2.rinterface_lib.callbacks.consoleread = my_consoleread
   

Write console
-------------

The function "write console" is called whenever output is sent to the R console.
In R's C API, there are two functions behind the hood, one for regular
printing, and one for warnings and errors.

.. autofunction:: rpy2.rinterface_lib.callbacks.consolewrite_print
.. autofunction:: rpy2.rinterface_lib.callbacks.consolewrite_warnerror

An example should make it obvious:

.. code-block:: python

   buf = []
   def f(x):
       # function that append its argument to the list 'buf'
       buf.append(x)

   # output from the R console will now be appended to the list 'buf'
   consolewrite_print_backup = rpy2.rinterface_lib.callbacks.consolewrite_print
   rpy2.rinterface_lib.callbacks.consolewrite_print = f

   date = rinterface.baseenv['date']
   rprint = rinterface.baseenv['print']
   rprint(date())

   # the output is in our list (as defined in the function f above)
   print(buf)

   # restore default function
   rpy2.rinterface_lib.callbacks.consolewrite_print = consolewrite_print_backup

.. autofunction:: rpy2.rinterface_lib.callbacks.consolewrite_print

Show message
------------

.. autofunction:: rpy2.rinterface_lib.callbacks.showmessage


Flush console
-------------

The function "flush console" is called whenever output is sent to the R console.

.. autofunction:: rpy2.rinterface_lib.callbacks.consoleflush

Yes/No/Cancel
-------------

.. autofunction:: rpy2.rinterface_lib.callbacks.yesnocancel


Files
=====

Showing files
-------------

.. autofunction:: rpy2.rinterface_lib.callbacks.showfiles

Choosing files
--------------

File choosing a on basic R console has very little bells and whistles.

.. code-block:: python

   def choose_csv(prompt):
       print(prompt)
       return(filename)


Other
=====

Process events
--------------

.. autofunction:: rpy2.rinterface_lib.callbacks.processevents

Busy
----

.. autofunction:: rpy2.rinterface_lib.callbacks.busy


.. _rinterface-callbacks_cleanup:

Clean up
--------

When asked to terminate, through either its terminal console
win32 or quartz GUI front-end, *R* will perform a cleanup operation
at the begining of which whether the user wants to save the workspace
or not.

What is happening during that cleaning step can be specified through
a callback function that will take three parameters *saveact*, *status*,
and *runlast*, return of 1 (save the workspace), 
0 (do not save the workspace), and None (cancel the exit/cleanup, raising
an :class:`RRuntimeError`).


.. code-block:: python

  import rpy2.rinterface

  rpy2.rinterface.initr()

  rquit = rpy2.rinterface.baseenv['q']

  def my_cleanup(saveact, status, runlast):
      # cancel all attempts to quit R programmatically
      print("One can't escape...")
      return None


>>> orig_cleanup = rpy2.rinterface_lib.callbacks.cleanup
>>> rpy2.rinterface_lib.callbacks.cleanup = my_cleanup
>>> rquit()

Restore the original cleanup:

>>> rpy2.rinterface_lib.callbacks.cleanup = orig_cleanup
