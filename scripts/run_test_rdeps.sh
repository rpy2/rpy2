#!/bin/bash
set -x

pytest \
    --cache-clear \
    --cov-append \
    --cov-report=xml \
    --cov-report=term \
    --cov=rpy2.rinterface_lib \
    --cov=rpy2.rinterface \
    --cov=rpy2.rlike \
    --cov=rpy2.robjects \
    --cov=rpy2.robjects.lib \
    rpy2-robjects/src/rpy2/robjects/tests/robjects/lib/
