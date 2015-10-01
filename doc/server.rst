.. _misc-server:

*************
Client-Server
*************

Rserve is currently the default solution when looking
for a server solution for R, but :mod:`rpy2` can be used
to develop very easily one's own server, tailored to answer
specific requirements. Such requirements can include for example
access restriction, a security model, access to subsets of the R
engine, distribution of jobs to other servers, all of which
are currently difficult or impossible to achieve with R serve.


The :mod:`pyRserve` package addresses the connection to Rserve
from Python, and although it frees one from handling the R server is
also constrains one to use Rserve.


Simple socket-based server and client
=====================================

Server
------

An implementation of a simplistic socket server listening
on a given port for a string to evaluate as R code
is straightforward with Python's SocketServer module.

Our example server will be in a file `rpyserve.py`, containing
the following code.

.. literalinclude:: _static/demos/rpyserve.py


Running a server listening on port 9090 is then:

.. code-block:: bash

   python rpyserve.py --hostname localhost


Client
------

Using Python's socket module, implementing a client is
just as easy. We write the code for ours into a file
`rpyclient.py`:
 
.. literalinclude:: _static/demos/rpyclient.py


Evaluating R code on a local server as defined in the previous
section, listening on port 9090 is then:

.. code-block:: bash

   echo 'R.version' | python rpyclient.py --hostname localhost

In this example, the client is querying the R version.

