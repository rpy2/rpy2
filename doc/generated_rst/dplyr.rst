
dplyr in Python
===============

We need 2 things for this:

1- A data frame (using one of R's demo datasets).

.. code:: python

    from rpy2.robjects.packages import importr, data
    datasets = importr('datasets')
    mtcars_env = data(datasets).fetch('mtcars')
    mtcars = mtcars_env['mtcars']

In addition to that, and because this tutorial is in a notebook, we
initialize HTML rendering for R objects (pretty display of R data
frames).

.. code:: python

    import rpy2.ipython.html
    rpy2.ipython.html.init_printing()

2- dplyr

.. code:: python

    from rpy2.robjects.lib.dplyr import DataFrame

With this we have the choice of chaining (D3-style)

.. code:: python

    dataf = (DataFrame(mtcars).
             filter('gear>3').
             mutate(powertoweight='hp*36/wt').
             group_by('gear').
             summarize(mean_ptw='mean(powertoweight)'))
    
    dataf




.. raw:: html

    
    <emph>DataFrame</emph> with 2 rows and 2 columns:
    <table class="rpy2_table">
      <thead>
        <tr class="rpy2_names">
          <th></th>
          <th></th>
          <th>gear</th>
          <th>mean_ptw</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="rpy2_rowname">0</td>
            <td class="rpy2_names">1</td>
          <td>4.0</td>
          <td>1237.1266499803169</td>
        </tr>
        <tr>
          <td class="rpy2_rowname">1</td>
            <td class="rpy2_names">2</td>
          <td>5.0</td>
          <td>2574.0331639315027</td>
        </tr>
      </tbody>
    </table>



or piping (magrittr style).

.. code:: python

    from rpy2.robjects.lib.dplyr import (filter,
                                         mutate,
                                         group_by,
                                         summarize)
    
    dataf = (DataFrame(mtcars) >>
             filter('gear>3') >>
             mutate(powertoweight='hp*36/wt') >>
             group_by('gear') >>
             summarize(mean_ptw='mean(powertoweight)'))
    
    dataf




.. raw:: html

    
    <emph>DataFrame</emph> with 2 rows and 2 columns:
    <table class="rpy2_table">
      <thead>
        <tr class="rpy2_names">
          <th></th>
          <th></th>
          <th>gear</th>
          <th>mean_ptw</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="rpy2_rowname">0</td>
            <td class="rpy2_names">1</td>
          <td>4.0</td>
          <td>1237.1266499803169</td>
        </tr>
        <tr>
          <td class="rpy2_rowname">1</td>
            <td class="rpy2_names">2</td>
          <td>5.0</td>
          <td>2574.0331639315027</td>
        </tr>
      </tbody>
    </table>



The strings passed to the dplyr function are evaluated as expression,
just like this is happening when using dplyr in R. This means that when
writing ``mean(powertoweight)`` the R function ``mean()`` is used.

Using an Python function is not too difficult though. We can just call
Python back from R:

.. code:: python

    from rpy2.rinterface import rternalize
    @rternalize
    def mean_np(x):
        import numpy
        return numpy.mean(x)
    
    from rpy2.robjects import globalenv
    globalenv['mean_np'] = mean_np
    
    dataf = (DataFrame(mtcars) >>
             filter('gear>3') >>
             mutate(powertoweight='hp*36/wt') >>
             group_by('gear') >>
             summarize(mean_ptw='mean(powertoweight)',
                       mean_np_ptw='mean_np(powertoweight)'))
    
    dataf




.. raw:: html

    
    <emph>DataFrame</emph> with 2 rows and 3 columns:
    <table class="rpy2_table">
      <thead>
        <tr class="rpy2_names">
          <th></th>
          <th></th>
          <th>gear</th>
          <th>mean_ptw</th>
          <th>mean_np_ptw</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="rpy2_rowname">0</td>
            <td class="rpy2_names">1</td>
          <td>4.0</td>
          <td>1237.1266499803169</td>
          <td>1237.126649980317</td>
        </tr>
        <tr>
          <td class="rpy2_rowname">1</td>
            <td class="rpy2_names">2</td>
          <td>5.0</td>
          <td>2574.0331639315027</td>
          <td>2574.0331639315023</td>
        </tr>
      </tbody>
    </table>



It is also possible to carry this out without having to place the custom
function in R's global environment.

.. code:: python

    del(globalenv['mean_np'])

.. code:: python

    from rpy2.robjects.lib.dplyr import StringInEnv
    from rpy2.robjects import Environment
    my_env = Environment()
    my_env['mean_np'] = mean_np
    
    dataf = (DataFrame(mtcars) >>
             filter('gear>3') >>
             mutate(powertoweight='hp*36/wt') >>
             group_by('gear') >>
             summarize(mean_ptw='mean(powertoweight)',
                       mean_np_ptw=StringInEnv('mean_np(powertoweight)',
                                               my_env)))
    
    dataf




.. raw:: html

    
    <emph>DataFrame</emph> with 2 rows and 3 columns:
    <table class="rpy2_table">
      <thead>
        <tr class="rpy2_names">
          <th></th>
          <th></th>
          <th>gear</th>
          <th>mean_ptw</th>
          <th>mean_np_ptw</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="rpy2_rowname">0</td>
            <td class="rpy2_names">1</td>
          <td>4.0</td>
          <td>1237.1266499803169</td>
          <td>1237.126649980317</td>
        </tr>
        <tr>
          <td class="rpy2_rowname">1</td>
            <td class="rpy2_names">2</td>
          <td>5.0</td>
          <td>2574.0331639315027</td>
          <td>2574.0331639315023</td>
        </tr>
      </tbody>
    </table>



**note**: rpy2's interface to dplyr is implementing a fix to the
(non-?)issue 1323 (https://github.com/hadley/dplyr/issues/1323)

The seamless translation of transformations to SQL whenever the data are
in a table can be used directly. Since we are lifting the original
implementation of ``dplyr``, it *just works*.

.. code:: python

    from rpy2.robjects.lib.dplyr import dplyr
    # in-memory SQLite database broken in dplyr's src_sqlite
    # db = dplyr.src_sqlite(":memory:")
    import tempfile
    with tempfile.NamedTemporaryFile() as db_fh:
        db = dplyr.src_sqlite(db_fh.name)
        # copy the table to that database
        dataf_db = DataFrame(mtcars).copy_to(db, name="mtcars")
        res = (dataf_db >>
               filter('gear>3') >>
               mutate(powertoweight='hp*36/wt') >>
               group_by('gear') >>
               summarize(mean_ptw='mean(powertoweight)'))
        print(res)
    # 


.. parsed-literal::

    Source: sqlite 3.8.6 [/tmp/tmp2nueqllw]
    From: <derived table> [?? x 2]
    
        gear mean_ptw
       (dbl)    (dbl)
    1      4 1237.127
    2      5 2574.033
    ..   ...      ...
    


Since we are manipulating R objects, anything available to R is also
available to us. If we want to see the SQL code generated that's:

.. code:: python

    print(res.rx2("query")["sql"])


.. parsed-literal::

    <SQL> SELECT "gear", "mean_ptw"
    FROM (SELECT "gear", AVG("powertoweight") AS "mean_ptw"
    FROM (SELECT "mpg", "cyl", "disp", "hp", "drat", "wt", "qsec", "vs", "am", "gear", "carb", "hp" * 36.0 / "wt" AS "powertoweight"
    FROM "mtcars"
    WHERE "gear" > 3.0) AS "zzz1"
    GROUP BY "gear") AS "zzz2"
    


And if the starting point is a pandas data frame, do the following and
start over again.

.. code:: python

    from rpy2.robjects import pandas2ri
    from rpy2.robjects import default_converter
    from rpy2.robjects.conversion import localconverter
    with localconverter(default_converter + pandas2ri.converter) as cv:
        mtcars = mtcars_env['mtcars']
        mtcars = pandas2ri.ri2py(mtcars)
    print(type(mtcars))


.. parsed-literal::

    <class 'pandas.core.frame.DataFrame'>


Using a local converter let's us also go from the pandas data frame to
our dplyr-augmented R data frame.

.. code:: python

    with localconverter(default_converter + pandas2ri.converter) as cv:
        dataf = (DataFrame(mtcars).
                 filter('gear>=3').
                 mutate(powertoweight='hp*36/wt').
                 group_by('gear').
                 summarize(mean_ptw='mean(powertoweight)'))
    
    dataf




.. raw:: html

    
    <emph>DataFrame</emph> with 3 rows and 2 columns:
    <table class="rpy2_table">
      <thead>
        <tr class="rpy2_names">
          <th></th>
          <th></th>
          <th>gear</th>
          <th>mean_ptw</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="rpy2_rowname">0</td>
            <td class="rpy2_names">1</td>
          <td>3.0</td>
          <td>1633.989574118287</td>
        </tr>
        <tr>
          <td class="rpy2_rowname">1</td>
            <td class="rpy2_names">2</td>
          <td>4.0</td>
          <td>1237.1266499803169</td>
        </tr>
        <tr>
          <td class="rpy2_rowname">2</td>
            <td class="rpy2_names">3</td>
          <td>5.0</td>
          <td>2574.0331639315027</td>
        </tr>
      </tbody>
    </table>



**Reuse. Get things done. Don't reimplement.**
