This is the source tree or distribution for the rpy2 package.

.. image:: https://drone.io/bitbucket.org/rpy2/rpy2/status.png
        :target: https://drone.io/bitbucket.org/rpy2/rpy2/latest

.. image:: https://img.shields.io/pypi/v/rpy2.svg?style=flat-square
        :target: https://pypi.python.org/pypi/rpy2


Installation
============

`pip` should work out of the box:

    pip install rpy2

The package is known to compile on Linux, MacOSX, and Windows
(provided that developper tools installed are you are ready figure out how yourself).

In case you find yourself with this source without any idea
of what it takes to compile anything on your platform, try first

    python setup.py install

If this fails, consider looking for pre-compiled binaries (they are available on Linux Red Hat,
CentOS, Debian, Ubuntu, etc...) or using the matching Docker container.

Note that `python setup.py develop` will appear to work, but will result in an
installation from the `rpy` directory here. The namespaces will be
incorrect, so don't do that!

Documentation
=============

Documentation is available either in the source tree (to be built),
or online (see the rpy home page on sourceforge).

Testing
=======

The testing machinery uses the new unittest functionality, requiring python 2.7+
(or potentially the backported unittest2 library for older python, but this is
not supported). The test suite can be run (once rpy2 is installed) as follows:

    python -m rpy2.tests

By providing an argument, like "-v", you'll get verbose output.

Individual tests can be run as follows:

    python -m unittest rpy2.robjects.tests.testVector

Test discovery can be attempted as follows (not that it may not work):

    python -m unittest discover rpy2.robjects

Prefer `python -m rpy2.tests` to run all tests.

License
=======

RPy2 can be used under the terms of either the GNU
General Public License Version 2 or later (see the file
gpl-2.0.txt).