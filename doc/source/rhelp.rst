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
for the function `sum` in the R package `base` becomes a matter of finding
where in the documentation the alias `sum` is found and retrieving it.

Querying on aliases
-------------------

When working with R, a frequent use case for using the documention
is to query on an alias (a function name, a dataset, or a class name)
and retrieve the associated documentation.

To do so with rpy2's interface to the help system, the easiest is to
use the function :func:`pages`. The function return a :class:`tuple`
of :class:`Page` instances.

.. autofunction:: rpy2.robjects.help.pages(topic)


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


>>> hp = base_help.fetch('sum')

>>> hp.sections.keys()
('title', 'name', 'alias', 'keyword', 'description', 'usage', 'arguments', 'deta
ils', 'value', 'section', 'references', 'seealso')

.. note::

   >>> print(''.join(hp.to_docstring(('details',))))

   ::

     details
     -------


        This is a generic function: methods can be defined for it
        directly or via the  Summary  group generic.
        For this to work properly, the arguments   should be
        unnamed, and dispatch is on the first argument.
 
        If  na.rm  is  FALSE  an  NA 
        value in any of the arguments will cause
        a value of  NA  to be returned, otherwise
        NA  values are ignored.
 
        Logical true values are regarded as one, false values as zero.
        For historical reasons,  NULL  is accepted and treated as if it
        were  integer(0) .
 


