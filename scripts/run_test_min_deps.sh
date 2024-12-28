#!/bin/bash
set -e
set -x

pytest \
    --cov-report=xml \
    --cov-report=term \
    --cov=rpy2.rinterface_lib \
    --cov=rpy2.rinterface \
    --cov=rpy2.rlike \
    --cov=rpy2.ipython \
    --cov=rpy2.robjects \
    ./rpy2-rinterface/src/rpy2/rinterface/tests \
    ./rpy2-robjects/src/rpy2/robjects/tests

pytest \
    --cov-append \
    --cov-report=xml \
    --cov-report=term \
    --cov=rpy2.rinterface_lib.embedded \
    ./rpy2-rinterface/src/rpy2/rinterface/tests/test_noinitialization.py

pytest \
    --cov-append \
    --cov-report=xml \
    --cov-report=term \
    --cov=rpy2.rinterface_lib.embedded \
    ./rpy2-rinterface/src/rpy2/rinterface/tests/test_endr.py

pytest \
    --cov-append \
    --cov-report=xml \
    --cov-report=term \
    --cov=rpy2.rinterface_lib.embedded \
    ./rpy2-rinterface/src/rpy2/rinterface/tests/test_threading.py
