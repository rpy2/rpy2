
tidyr in Python
===============

.. code:: python

    from rpy2.robjects.lib.tidyr import DataFrame

(note: ``dplyr`` is implicitly used by ``tidyr``.)

In addition to that, and because this tutorial is in a notebook, we
initialize HTML rendering for R objects (pretty display of R data
frames).

.. code:: python

    import rpy2.ipython.html
    rpy2.ipython.html.init_printing()

.. code:: python

    from rpy2.robjects.vectors import (StrVector,
                                       IntVector)
    dataf = DataFrame({'x': StrVector(("a", "b")),
                       'y': IntVector((3, 4)),
    		   'z': IntVector((5, 6))})
    dataf




.. raw:: html

    
    <emph>DataFrame</emph> with 2 rows and 3 columns:
    <table class="rpy2_table">
      <thead>
        <tr class="rpy2_names">
          <th></th>
          <th></th>
          <th>y</th>
          <th>z</th>
          <th>x</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="rpy2_rowname">0</td>
            <td class="rpy2_names">1</td>
          <td>3</td>
          <td>5</td>
          <td>a</td>
        </tr>
        <tr>
          <td class="rpy2_rowname">1</td>
            <td class="rpy2_names">2</td>
          <td>4</td>
          <td>6</td>
          <td>b</td>
        </tr>
      </tbody>
    </table>



.. code:: python

    dataf.spread('x', 'y')




.. parsed-literal::

    '  z  a  b\n1 5  3 NA\n2 6 NA  4\n'



**Reuse. Get things done. Don't reimplement.**
