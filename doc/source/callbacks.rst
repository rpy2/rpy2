*********
Callbacks
*********

Although R has been tightly bound to its console, the R-core development team has
great progress in letting front-end developpers customize R's interactive behavior
to their needs.

:mod:`rpy2` is offering to customize R's interactive behavior through callback functions.

Console I/O
===========

During an interactive session, much of the communication between R and the user happen
happen through the console. How the console reads input and writes output, can be
defined through callback functions.

Read console
------------

The 'read console' function is called whenever console input is expected.

A suitable callback function will be such as it accepts one parameter of class :class:`str`,
that is the prompt, and returns the user input as a :class:`str`.

The pair of functions 
:func:`rpy2.rinterface.setReadConsole` and :func:`rpy2.rinterface.getReadConsole`
can be used to set and retrieve the callback function respectively.

Write console
-------------

The 'write console' function is called whenever output is sent to the R console.

A suitable callback function will be such as it accepts one parameter of class :class:`str`
and only has side-effects (does not return anything).

The pair of functions 
:func:`rpy2.rinterface.setWriteConsole` and :func:`rpy2.rinterface.getWriteConsole`
can be used to set and retrieve the callback function respectively.


Flush console
-------------

The 'write console' function is called whenever output is sent to the R console.

A suitable callback function will be such as it accepts no parameter
and only has side-effects (does not return anything).

The pair of functions 
:func:`rpy2.rinterface.setFlushConsole` and :func:`rpy2.rinterface.getFlushConsole`
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
