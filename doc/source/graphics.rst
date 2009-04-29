********
Graphics
********

Introduction
============

This section shows how to make R graphics from rpy2, 
using some of the different graphics systems available to R users.

The purpose of this section is to get users going, and be able to figure out
by reading the R documentation how to perform the same plot in rpy2.


Graphical devices
-----------------

With `R`, all graphics are plotted into a so-called graphical device.
Graphical devices can be interactive, like for example `X11`, 
or non-interactive, like `png` or `pdf`. Non-interactive devices
appear to be files.

By default an interactive R session will open an interactive device
when needing one. If a non-interactive graphical device is needed,
one will have to specify it.

.. note::

   Do not forget to close a non-interactive device when done.
This will flush the writing to the file.


Getting ready
-------------

To run examples in this section we first import
:mod:`rpy2.robjects` and define few helper
functions.

.. literalinclude:: _static/demos/graphics.py
   :lines: 2-12


Package *lattice*
=================


Introduction
------------


Importing the package `lattice` is done the
same as it is done for other R packages.

.. literalinclude:: _static/demos/graphics.py
   :lines: 16-18

Scatter plot
------------

We use the dataset *mtcars*, and will use
the lattice function *xyplot* to make scatter plots.

.. literalinclude:: _static/demos/graphics.py
   :lines: 28-31

Lattice is working with formulae, we build
one and store values in its environment.
Making a plot is then a matter of calling
the function *xyplot* with the *formula* as
as argument.

.. literalinclude:: _static/demos/graphics.py
   :lines: 33-38

.. image:: _static/graphics_lattice_xyplot_1.png
   :scale: 50


The display of group information can be done
simply by using the named parameter groups.
This will indicate the different groups by
color-coding.

.. literalinclude:: _static/demos/graphics.py
   :lines: 45-46

.. image:: _static/graphics_lattice_xyplot_2.png
   :scale: 50

An alternative to color-coding is to have 
points is different *panels*. In lattice,
this done by specify it in the formula.

.. literalinclude:: _static/demos/graphics.py
   :lines: 53-59

.. image:: _static/graphics_lattice_xyplot_3.png
   :scale: 50

Package *ggplot2*
=================

Introduction
------------

.. literalinclude:: _static/demos/graphics.py
   :lines: 65-69




Plot
----

.. literalinclude:: _static/demos/graphics.py
   :lines: 76-82

.. image:: _static/graphics_ggplot2_qplot_1.png
   :scale: 50

.. literalinclude:: _static/demos/graphics.py
   :lines: 89-96

.. image:: _static/graphics_ggplot2_qplot_2.png
   :scale: 50

.. literalinclude:: _static/demos/graphics.py
   :lines: 104-119
   
.. image:: _static/graphics_ggplot2_ggplot_1.png
   :scale: 50

Adding graphical elements
^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: _static/demos/graphics.py
   :lines: 127-135
   
.. image:: _static/graphics_ggplot2_qplot_3.png
   :scale: 50


.. literalinclude:: _static/demos/graphics.py
   :lines: 142-143
   
.. image:: _static/graphics_ggplot2_qplot_4.png
   :scale: 50


.. literalinclude:: _static/demos/graphics.py
   :lines: 151-154
   
.. image:: _static/graphics_ggplot2_qplot_5.png
   :scale: 50


.. literalinclude:: _static/demos/graphics.py
   :lines: 162-164
   
.. image:: _static/graphics_ggplot2_qplot_6.png
   :scale: 50


.. literalinclude:: _static/demos/graphics.py
   :lines: 171-173
   
.. image:: _static/graphics_ggplot2_qplot_7.png
   :scale: 50


.. literalinclude:: _static/demos/graphics.py
   :lines: 181-185
   
.. image:: _static/graphics_ggplot2_ggplot_add.png
   :scale: 50


