.. module:: rpy2.robjects.help
   :platform: Unix, Windows
   :synopsis: High-level interface with R

R help
======

`R` has a documentation system that ensures that documentation for code
distributed as packages is installed when packages are installed.
This documentation can be called and searched for from R itself.

Unlike `Python` docstrings the R documentation lives outside
objects, and is organised on documentation pages. Each documentation
page has `aliases`, and often aliases are corresponding to the names of
R objects defined in a package. This way, querying the documentation
for the function `sum` in the R package `base` becomes a matter of calling
the topic `sum`.

Package documentation
---------------------

The documentation for a package is represented with the class
:class:`Package`.

.. autoclass:: rpy2.robjects.help.Package(package_name, package_path = None)
   :show-inheritance:
   :members:


>>> import rpy2.robjects.help as rh
>>> base_help = rh.Package('base')
>>> base_help.fetch('sum')

Documentation page
------------------

A particular documentation page is represented as an instance of
class :class:`Page`

.. autoclass:: rpy2.robjects.help.Page(struct_rdb)
   :show-inheritance:
   :members:


>>> hp = rh.Page(base_help.fetch('sum'))

>>> print(ho.to_docstrings())

