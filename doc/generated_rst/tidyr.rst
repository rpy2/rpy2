
.. code:: python

    from functools import partial
    from rpy2.ipython import html
    html.html_rdataframe=partial(html.html_rdataframe, table_class="docutils")

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

    from collections import OrderedDict
    from rpy2.robjects.vectors import (StrVector,
                                       IntVector)
    dataf = DataFrame(OrderedDict(x=StrVector(("a", "b", "b")),
                                  y=IntVector((3, 4, 5)),
    		              z=IntVector((6, 7, 8))))
    dataf




.. raw:: html

    
    <emph>DataFrame</emph> with 3 rows and 3 columns:
    <table class="docutils">
      <thead>
        <tr class="rpy2_names">
          <th></th>
          <th></th>
          <th>z</th>
          <th>x</th>
          <th>y</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="rpy2_rowname">0</td>
            <td class="rpy2_names">1</td>
          <td>6</td>
          <td>a</td>
          <td>3</td>
        </tr>
        <tr>
          <td class="rpy2_rowname">1</td>
            <td class="rpy2_names">2</td>
          <td>7</td>
          <td>b</td>
          <td>4</td>
        </tr>
        <tr>
          <td class="rpy2_rowname">2</td>
            <td class="rpy2_names">3</td>
          <td>8</td>
          <td>b</td>
          <td>5</td>
        </tr>
      </tbody>
    </table>



.. code:: python

    dataf.spread('x', 'y')




.. raw:: html

    
    <emph>DataFrame</emph> with 3 rows and 3 columns:
    <table class="docutils">
      <thead>
        <tr class="rpy2_names">
          <th></th>
          <th></th>
          <th>z</th>
          <th>a</th>
          <th>b</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="rpy2_rowname">0</td>
            <td class="rpy2_names">1</td>
          <td>6</td>
          <td>3</td>
          <td>NA</td>
        </tr>
        <tr>
          <td class="rpy2_rowname">1</td>
            <td class="rpy2_names">2</td>
          <td>7</td>
          <td>NA</td>
          <td>4</td>
        </tr>
        <tr>
          <td class="rpy2_rowname">2</td>
            <td class="rpy2_names">3</td>
          <td>8</td>
          <td>NA</td>
          <td>5</td>
        </tr>
      </tbody>
    </table>



**Reuse. Get things done. Don't reimplement.**
