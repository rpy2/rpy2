.. _graphicaldevices-custom:

Custom graphical devices
------------------------

.. warning::

   This is still very experimental, and using this may result in
   crashing the Python interpreter.

The C-API to R allows extension writers to implement custom
graphical devices (using C). This feature was used to implement
drivers to SVG or Cairo, for example (Cairo support made it later to the R
codebase).

Rpy2 is exposing the creation of custome graphical devies to Python
programmer, without the need for C.

To demonstrate how to implement a graphical, we consider the following
example:
a device that counts the number of times graphical primitives are used.
This is something of very limited practical use, but enough to explain
the principles.

Such a device would be implemented as follows:

.. code-block:: python

   import rpy2.rinterface._rpy_device as rdevice
   from collections import Counter

   class BeancounterDevice(rdevice.GraphicalDevice):
       """ Graphical devive for R that counts the
       number of times primitives are called."""

       def __init__(self):
           super(BeancounterDevice, self).__init__()
           self._ct = Counter()

       def circle(self, x, y, radius):
           self._ct['circle'] += 1

       def clip(self, x0, x1, y0, y1):
           self._ct['clip'] += 1

       def line(self, x1, y1, x2, y2):
           self._ct['lines'] += 1

       def mode(self, mode):
           self._ct['mode'] += 1

       def rect(self, x0, x1, y0, y1):
           self._ct['rectangle'] += 1

       def strwidth(self, text):
           self._ct['strwidth'] += 1
           return float(0)

       def text(x, y, string, rot, hadj):
           self._ct['text'] += 1

The class :class:`BeancounterDevice` can now be used as genuine
R plotting device.

.. code-block:: python

   from rpy2.robjects.packages import importr

   dev = BeancounterDevice()

   graphics = importr("graphics")
   # plot into our counting device
   graphics.plot(0, 0)

   # Print the counts
   print(dev._ct)


To implement a new custom graphical device for R, one only has to
extend the class :class:`rpy2.rinterface._rpy_device.GraphicalDevice`.
Error messages will be printed if that new device does not implement
functionalities used by R.

The Python documentation strings for the class and its methods are:

.. autoclass:: rpy2.rinterface._rpy_device.GraphicalDevice
   :members:
