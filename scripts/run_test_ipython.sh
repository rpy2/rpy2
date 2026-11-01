#!/bin/bash
set -e
set -x

pytest \
    --cov-append \
    --cov-report=xml \
    --cov-report=term \
    --cov=rpy2.rinterface_lib \
    --cov=rpy2.rinterface \
    --cov=rpy2.rlike \
    --cov=rpy2.ipython \
    --cov=rpy2.robjects \
    ./rpy2-robjects/src/rpy2/ipython
