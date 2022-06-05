Documentation for rpy2
======================


.. ifconfig:: release.endswith('dev') or release[:-1].endswith('alpha')

   .. warning::
      This documentation describe the rpy2 package version |version| on |today|.
      It is still under development. While care is taken to keep the
      development branch functional
      at all times, and this documentation up-to-date temporary issues
      may appear.
      Please remember that this is software under development.

      Use a released version of the package for production.


.. only:: html

   .. image:: _static/rpy2_logo.png


.. only:: html

   The first section contains a quick introduction, as well as how to get started
   (requirements, install rpy2). This should be the natural place to
   start if you are new to R, or rpy2. Hints for porting existing code to a newer
   version of rpy2 are also given.

   .. toctree::
      :maxdepth: 3

      getting-started
      porting-to-rpy2

   The high-level interface in rpy2 is designed to facilitate the use of R by
   Python programmers. R objects are exposed as instances of Python-implemented
   classes, with R functions as bound methods to those objects in a number of cases.
   This section also contains an introduction to graphics with R: *trellis* (*lattice*)
   plots as well as the grammar of graphics implemented in *ggplot2* let one
   make complex and informative plots with little code written, while the underlying
   *grid* graphics allow all possible customization is outlined.

   .. toctree::
      :maxdepth: 3

      high-level
   
   R is often used in a read-eval-print loop (REPL), where interactivity is important.
   Utilities are available in :mod:`rpy2.interactive`.

   .. toctree::
      :maxdepth: 3

      interactive

   Users of the Python signature numerical package :mod:`numpy` can continue using
   the data structures they are familiar with, and share objects seamlessly with R.

   .. toctree::
      :maxdepth: 3

      numpy

   A lower-level interface, closer to R's C-level API, is available. It can be used
   when performance optimization is needed, or when extensions to the high-level
   interface are developped.

   .. toctree::
      :maxdepth: 3

      rinterface
      rinterface-memorymanagement

   Finally, the documentation covers the subpackage with R-like Python classes
   and functions, callback functions, as well as compatibility with rpy-1.x.
   and benchmarks.

   .. toctree::
      :maxdepth: 3

      rlike
      miscellaneous


   The list of changes across versions can be helpful when
   upgrading to a newer version of rpy2.

   .. toctree::
      :maxdepth: 2

      appendix


