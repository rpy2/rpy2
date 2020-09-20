#!/bin/bash

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
