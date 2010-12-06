.. module:: rpy2.interactive

****************
Interactive work
****************

Overview
========

R is very often used as an interactive toplevel, or read-eval-print loop (REPL).
When analyzing data this is kind of environment is extremely convenient as
the analyst often does not know beforehand what lies in the data and how this
is going to be discovered.

Python is can also be used in a similar fashion, but limitations of the
default Python console have lead to the creation of alternative consoles
and interactive development editors
(idle, ipython, bpython, pymacs in emacs, komodo, ...).


.. module:: rpy2.interactive.process_revents

R event loop
============

In order to perform operations like refreshing interactive graphical
devices, R need to process the events triggering the refresh.

>>> from rpy2.interactive import process_revents
>>> process_revents.start()

>>> from rpy2.robjects.packages import importr
>>> from rpy2.robjects.vectors import IntVector
>>> graphics = importr("graphics")
>>> graphics.barplot(IntVector((1,3,2,5,4)), ylab="Value")

Now the R graphical device is updated when resized.

>>> process_revents.stop()

The frequency with which the processing of R events is performed can be roughly
controlled. The thread is put to sleep for an arbitray duration between
each processing of R events.

>>> process_revents.EventProcessor.interval
0.2

This value can be changed and set to an other value if more or less frequent
processing is wished. This can be done while the threaded processing is
active and will be taken into account at the next sleep cycle.

>>> process_revents.EventProcessor.interval = 1.0


Graphical User interface
========================


