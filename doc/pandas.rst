.. _robjects-pandas:

****************************
Interoperability with pandas
****************************

This section of the documentation is focused on the practical use of the conversion
helper for :mod:`pandas`. The conversion from and to :class:`pandas.DataFrame`
can create nonnegligible overhead as the C level representations for the underlying
arrays may differ between Python and R, and this create the need to copy data from
one representation to the other. This is the case for arrays of strings for example.
The use of a local converter to limit the scope of conversions, as shown here, is
recommended.

For more information about the conversion mechanism, check the more general documentation
about :mod:`rpy2.robjects.conversion`.

.. note::

   This section is available as a jupyter notebook `pandas.ipynb`_ (HTML render: `pandas.html`_)

   .. _pandas.ipynb: _static/notebooks/pandas.ipynb
   .. _pandas.html: _static/notebooks/pandas.html

.. include:: generated_rst/pandas.rst
