
.. code:: 

    from functools import partial
    from rpy2.ipython import html
    html.html_rdataframe=partial(html.html_rdataframe, table_class="docutils")

dplyr in Python
===============

We need 2 things for this:

1- A data frame (using one of R's demo datasets).

.. code:: 

    from rpy2.robjects.packages import importr, data
    datasets = importr('datasets')
    mtcars_env = data(datasets).fetch('mtcars')
    mtcars = mtcars_env['mtcars']

In addition to that, and because this tutorial is in a notebook, we
initialize HTML rendering for R objects (pretty display of R data
frames).

.. code:: 

    import rpy2.ipython.html
    rpy2.ipython.html.init_printing()

2- dplyr

.. code:: 

    from rpy2.robjects.lib.dplyr import DataFrame

With this we have the choice of chaining (D3-style)

.. code:: 

    dataf = (DataFrame(mtcars).
             filter('gear>3').
             mutate(powertoweight='hp*36/wt').
             group_by('gear').
             summarize(mean_ptw='mean(powertoweight)'))
    
    dataf




.. raw:: html

    
    <emph>DataFrame</emph> with 2 rows and 2 columns:
    <table class="docutils">
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



or with pipes (magrittr style).

.. code:: 

    # currently no longer working
    from rpy2.robjects.lib.dplyr import (filter,
                                         mutate,
                                         group_by,
                                         summarize)
    
    if False:
        dataf = (DataFrame(mtcars) >>
                 filter('gear>3') >>
                 mutate(powertoweight='hp*36/wt') >>
                 group_by('gear') >>
                 summarize(mean_ptw='mean(powertoweight)'))
    
        dataf

The strings passed to the dplyr function are evaluated as expression,
just like this is happening when using dplyr in R. This means that when
writing ``mean(powertoweight)`` the R function ``mean()`` is used.

Using a Python function is not too difficult though. We can just call
Python back from R. To achieve this we simply use the decorator
``rternalize``.

.. code:: 

    # Define a python function, and make
    # it a function R can use through `rternalize`
    from rpy2.rinterface import rternalize
    @rternalize
    def mean_np(x):
        import statistics
        return statistics.mean(x)
    
    # Bind that function to a symbol in R's
    # global environment
    from rpy2.robjects import globalenv
    globalenv['mean_np'] = mean_np
    
    # Write a dplyr chain of operations,
    # using our Python function `mean_np`
    dataf = (DataFrame(mtcars).
             filter('gear>3').
             mutate(powertoweight='hp*36/wt').
             group_by('gear').
             summarize(mean_ptw='mean(powertoweight)',
                       mean_np_ptw='mean_np(powertoweight)'))
    
    dataf




.. raw:: html

    
    <emph>DataFrame</emph> with 2 rows and 3 columns:
    <table class="docutils">
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
          <td>1237.1266499803169</td>
        </tr>
        <tr>
          <td class="rpy2_rowname">1</td>
            <td class="rpy2_names">2</td>
          <td>5.0</td>
          <td>2574.0331639315027</td>
          <td>2574.0331639315027</td>
        </tr>
      </tbody>
    </table>



It is also possible to carry this out without having to place the custom
function in R's global environment.

.. code:: 

    del(globalenv['mean_np'])

.. code:: 

    from rpy2.robjects.lib.dplyr import StringInEnv
    from rpy2.robjects import Environment
    my_env = Environment()
    my_env['mean_np'] = mean_np
    
    dataf = (DataFrame(mtcars).
             filter('gear>3').
             mutate(powertoweight='hp*36/wt').
             group_by('gear').
             summarize(mean_ptw='mean(powertoweight)',
                       mean_np_ptw=StringInEnv('mean_np(powertoweight)',
                                               my_env)))
    
    dataf




.. raw:: html

    
    <emph>DataFrame</emph> with 2 rows and 3 columns:
    <table class="docutils">
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
          <td>1237.1266499803169</td>
        </tr>
        <tr>
          <td class="rpy2_rowname">1</td>
            <td class="rpy2_names">2</td>
          <td>5.0</td>
          <td>2574.0331639315027</td>
          <td>2574.0331639315027</td>
        </tr>
      </tbody>
    </table>



**note**: rpy2's interface to dplyr is implementing a fix to the
(non-?)issue 1323 (https://github.com/hadley/dplyr/issues/1323)

The seamless translation of transformations to SQL whenever the data are
in a table can be used directly. Since we are lifting the original
implementation of ``dplyr``, it *just works*.

.. code:: 

    from rpy2.robjects.lib.dplyr import dplyr
    # in-memory SQLite database broken in dplyr's src_sqlite
    # db = dplyr.src_sqlite(":memory:")
    import tempfile
    with tempfile.NamedTemporaryFile() as db_fh:
        db = dplyr.src_sqlite(db_fh.name)
        # copy the table to that database
        dataf_db = DataFrame(mtcars).copy_to(db, name="mtcars")
        res = (dataf_db.
               filter('gear>3').
               mutate(powertoweight='hp*36/wt').
               group_by('gear').
               summarize(mean_ptw='mean(powertoweight)'))
        print(res)
    # 


.. parsed-literal::

    [90m# Source:   lazy query [?? x 2][39m
    [90m# Database: sqlite 3.22.0 [/tmp/tmpnd75g166][39m
       gear mean_ptw
      [3m[90m<dbl>[39m[23m    [3m[90m<dbl>[39m[23m
    [90m1[39m     4    [4m1[24m237.
    [90m2[39m     5    [4m2[24m574.
    


Since we are manipulating R objects, anything available to R is also
available to us. If we want to see the SQL code generated that's:

.. code:: 

    silent = dplyr.show_query(res)


.. parsed-literal::

    Callback to write to the R console: <SQL>
    SELECT `gear`, AVG(`powertoweight`) AS `mean_ptw`
    FROM (SELECT `mpg`, `cyl`, `disp`, `hp`, `drat`, `wt`, `qsec`, `vs`, `am`, `gear`, `carb`, `hp` * 36.0 / `wt` AS `powertoweight`
    FROM (SELECT *
    FROM `mtcars`
    WHERE (`gear` > 3.0)))
    GROUP BY `gear`
    


The conversion rules in rpy2 make the above easily applicable to pandas
data frames, completing the "lexical loan" of the dplyr vocabulary from
R.

.. code:: 

    from rpy2.robjects import pandas2ri
    from rpy2.robjects import default_converter
    from rpy2.robjects.conversion import localconverter
    
    # Using a conversion context in which the pandas conversion is
    # added to the default conversion rules, the rpy2 object
    # `mtcars` (an R data frame) is converted to a pandas data frame.
    with localconverter(default_converter + pandas2ri.converter) as cv:
        pd_mtcars = mtcars_env['mtcars']
    print(type(pd_mtcars))


.. parsed-literal::

    <class 'pandas.core.frame.DataFrame'>


.. parsed-literal::

    /home/laurent/Desktop/software/python/py36_env/lib/python3.6/site-packages/rpy2-3.0.0.dev0-py3.6.egg/rpy2/robjects/pandas2ri.py:196: FutureWarning: from_items is deprecated. Please use DataFrame.from_dict(dict(items), ...) instead. DataFrame.from_dict(OrderedDict(items)) may be used to preserve the key order.
      res = PandasDataFrame.from_items(items)


Using a local converter lets us also go from the pandas data frame to
our dplyr-augmented R data frame and use the dplyr transformations on
it.

.. code:: 

    with localconverter(default_converter + pandas2ri.converter) as cv:
        dataf = (DataFrame(pd_mtcars).
                 filter('gear>=3').
                 mutate(powertoweight='hp*36/wt').
                 group_by('gear').
                 summarize(mean_ptw='mean(powertoweight)'))
    
    dataf




.. raw:: html

    
    <emph>DataFrame</emph> with 1 rows and 1 columns:
    <table class="docutils">
      <thead>
        <tr class="rpy2_names">
          <th></th>
          <th></th>
          <th>mean_ptw</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="rpy2_rowname">0</td>
            <td class="rpy2_names">0</td>
          <td>1632.0477884748632</td>
        </tr>
      </tbody>
    </table>



**Reuse. Get things done. Don't reimplement.**
