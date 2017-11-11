
.. code:: 

    from functools import partial
    from rpy2.ipython import html
    html.html_rdataframe=partial(html.html_rdataframe, table_class="docutils")

tidyr in Python
===============

.. code:: 

    from rpy2.robjects.lib.tidyr import DataFrame


.. parsed-literal::

    /home/laurent/Desktop/software/python/py35_env/lib/python3.5/site-packages/rpy2-3.0.0.dev0-py3.5-linux-x86_64.egg/rpy2/robjects/lib/tidyr.py:10: UserWarning: This was designed againt tidyr version 0.7.2 but you have 0.7.1
      warnings.warn('This was designed againt tidyr version %s but you have %s' % (TARGET_VERSION, tidyr.__version__))
    /home/laurent/Desktop/software/python/py35_env/lib/python3.5/site-packages/rpy2-3.0.0.dev0-py3.5-linux-x86_64.egg/rpy2/robjects/lib/dplyr.py:24: UserWarning: This was designed againt dplyr version 0.7.4 but you have 0.7.3
      warnings.warn('This was designed againt dplyr version %s but you have %s' % (TARGET_VERSION, dplyr.__version__))


(note: ``dplyr`` is implicitly used by ``tidyr``.)

In addition to that, and because this tutorial is in a notebook, we
initialize HTML rendering for R objects (pretty display of R data
frames).

.. code:: 

    import rpy2.ipython.html
    rpy2.ipython.html.init_printing()

.. code:: 

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
          <th>y</th>
          <th>x</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="rpy2_rowname">0</td>
            <td class="rpy2_names">1</td>
          <td>6</td>
          <td>3</td>
          <td>a</td>
        </tr>
        <tr>
          <td class="rpy2_rowname">1</td>
            <td class="rpy2_names">2</td>
          <td>7</td>
          <td>4</td>
          <td>b</td>
        </tr>
        <tr>
          <td class="rpy2_rowname">2</td>
            <td class="rpy2_names">3</td>
          <td>8</td>
          <td>5</td>
          <td>b</td>
        </tr>
      </tbody>
    </table>



.. code:: 

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
          <td>-2147483648</td>
        </tr>
        <tr>
          <td class="rpy2_rowname">1</td>
            <td class="rpy2_names">2</td>
          <td>7</td>
          <td>-2147483648</td>
          <td>4</td>
        </tr>
        <tr>
          <td class="rpy2_rowname">2</td>
            <td class="rpy2_names">3</td>
          <td>8</td>
          <td>-2147483648</td>
          <td>5</td>
        </tr>
      </tbody>
    </table>



**Reuse. Get things done. Don't reimplement.**
