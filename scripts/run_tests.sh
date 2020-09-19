#!/bin/bash

pip uninstall -y numpy
pip uninstall -y pandas

pytest \
    --cov-append \
    --cov-report=xml \
    --cov=rpy2.rinterface_lib \
    --cov=rpy2.rinterface \
    --cov=rpy2.rlike \
    --cov=rpy2.ipython \
    --cov=rpy2.robjects \
    rpy2/tests

pytest \
    --cov-append \
    --cov-report=xml \
    --cov=rpy2.rinterface_lib.embedded \
    rpy2/tests/rinterface/test_noinitialization.py

pytest \
    --cov-append \
    --cov-report=xml \
    --cov=rpy2.rinterface_lib.embedded \
    rpy2/tests/rinterface/test_endr.py

pip install numpy
pytest \
    --cov-append \
    --cov-report=xml \
    --cov=rpy2.rinterface_lib \
    --cov=rpy2.rinterface \
    --cov=rpy2.rlike \
    --cov=rpy2.ipython \
    --cov=rpy2.robjects \
    rpy2/tests

pip install pandas

pytest \
    --cov-append \
    --cov-report=xml \
    --cov=rpy2.rinterface_lib \
    --cov=rpy2.rinterface \
    --cov=rpy2.rlike \
    --cov=rpy2.ipython \
    --cov=rpy2.robjects \
    rpy2/tests

sudo Rscript ./install_r_packages.r ggplot2 dplyr tidyr dbplyr lazyeval rlang

pytest \
    --cache-clear \
    --cov-append \
    --cov-report=xml \
    --cov=rpy2.rinterface_lib \
    --cov=rpy2.rinterface \
    --cov=rpy2.rlike \
    --cov=rpy2.robjects \
    --cov=rpy2.robjects.lib \
    rpy2/tests/robjects/lib
