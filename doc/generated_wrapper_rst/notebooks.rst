***********************
Using rpy2 in notebooks
***********************

`rpy2` is designed to play well with notebooks. While the target
notebook is jupyter, it is used in other notebook systems (some of
them are based on `Jupyter`_, or are managed Jupyter notebook systems).

rpy2 is working, and is sometimes available by default, with
`Google's Colab`_,
`Databricks notebooks`_, `AWS SageMaker`_, `Azure Notebooks`_,
or `Google Cloud AI Platform Notebooks`_.

.. _`Jupyter`: https://jupyter.org/
.. _`Google's Colab`: https://research.google.com/colaboratory/faq.html
.. _`Databricks notebooks`: https://docs.databricks.com/notebooks/index.html
.. _`AWS SageMaker`: https://docs.aws.amazon.com/sagemaker/latest/dg/nbi.html
.. _`Azure Notebooks`: https://notebooks.azure.com/
.. _`Google Cloud AI Platform Notebooks`: https://cloud.google.com/ai-platform-notebooks

This section shows how `rpy2` can be used to add everything R can offer
to Python notebooks.

.. note::

   This section is available as a jupyter notebook `jupyter.ipynb`_ (HTML render: `jupyter.html`_)

   .. _jupyter.ipynb: _static/notebooks/jupyter.ipynb
   .. _jupyter.html: _static/notebooks/jupyter.html
   
.. include:: jupyter.rst
