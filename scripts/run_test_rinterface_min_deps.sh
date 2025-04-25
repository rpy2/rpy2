#!/bin/bash
set -e
set -x

pytest \
    --cov-report=xml \
    --cov-report=term \
    --cov=rpy2.rinterface_lib \
    --cov=rpy2.rinterface \
    --cov=rpy2.rlike \
    ./rpy2-rinterface/src/rpy2/rinterface/tests \

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
