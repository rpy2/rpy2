.. _rinterface-callbacks:

*********
Callbacks
*********

Although R has been tightly bound to its console, the R-core development team has
great progress in letting front-end developpers customize R's interactive behavior
to their needs.

:mod:`rpy2` is offering to customize R's interactive behavior through callback functions.

.. _rinterface-callbacks_consoleio:

Console I/O
===========

During an interactive session, much of the communication between R and the user happen
happen through the console. How the console reads input and writes output, can be
defined through callback functions.

Read console
------------

The 'read console' function is called whenever console input is expected.


The default callback for inputing data is :func:`rinterface.consoleRead`

.. autofunction:: rpy2.rinterface.consoleRead(prompt)

   :param prompt: :class:`str`
   :rtype: :class:`str`


A suitable callback function will be such as it accepts one parameter of class :class:`str`,
that is the prompt, and returns the user input as a :class:`str`.

The pair of functions 
:func:`rpy2.rinterface.set_readconsole` and :func:`rpy2.rinterface.get_readconsole`
can be used to set and retrieve the callback function respectively.

.. autofunction:: rpy2.rinterface.set_readconsole(f)

.. autofunction:: rpy2.rinterface.get_readconsole()

   :rtype: a callable


Write console
-------------

The 'write console' function is called whenever output is sent to the R console.

A suitable callback function will be such as it accepts one parameter of class :class:`str`
and only has side-effects (does not return anything).

The pair of functions 
:func:`rpy2.rinterface.set_writeconsole` and :func:`rpy2.rinterface.get_writeconsole`
can be used to set and retrieve the callback function respectively.

The default callback function, called :func:`rinterface.consolePrint`
is a simple write to :data:`sys.stdout`

.. autofunction:: rpy2.rinterface.consolePrint(x)

   :param x: :class:`str`
   :rtype: None

An example should make it obvious::

   buf = []
   def f(x):
       # function that append its argument to the list 'buf'
       buf.append(x)

   # output from the R console will now be appended to the list 'buf'
   rinterface.set_writeconsole(f)

   date = rinterface.baseenv['date']
   rprint = rinterface.baseenv['print']
   rprint(date())

   # the output is in our list (as defined in the function f above)
   print(buf)


   # restore default function
   rinterface.set_writeconsole(rinterface.consolePrint)


.. autofunction:: rpy2.rinterface.set_writeconsole(f)

.. autofunction:: rpy2.rinterface.get_writeconsole()

   :rtype: a callable


Flush console
-------------

The 'write console' function is called whenever output is sent to the R console.

A suitable callback function will be such as it accepts no parameter
and only has side-effects (does not return anything).

The pair of functions 
:func:`rpy2.rinterface.set_flushconsole` and :func:`rpy2.rinterface.get_flushconsole`
can be used to set and retrieve the callback function respectively.


Files
=====

Showing files
-------------


Choosing files
--------------

File choosing a on basic R console has very little bells and whistles.

.. code-block:: python

   def choose_csv(prompt):
       print(prompt)
       return(filename)


Other
=====

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

  def cleanup(saveact, status, runlast):
      # cancel all attempts to quit R programmatically
      print("One can't escape...")
      return None


>>>  orig_cleanup = rpy2.rinterface.get_cleanup()
>>>  rpy2.rinterface.set_cleanup(cleanup)
>>> rquit()


Restore the original cleanup:

>>> rpy2.rinterface.set_cleanup(orig_cleanup)
