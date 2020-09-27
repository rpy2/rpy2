#!/bin/bash

pytest \
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
