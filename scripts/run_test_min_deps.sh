#!/bin/bash
set -e

pytest \
    --cov-report=xml \
    --cov-report=term \
    --cov=rpy2.rinterface_lib \
    --cov=rpy2.rinterface \
    --cov=rpy2.rlike \
    --cov=rpy2.ipython \
    --cov=rpy2.robjects \
    ./rpy2/tests

pytest \
    --cov-append \
    --cov-report=xml \
    --cov-report=term \
    --cov=rpy2.rinterface_lib.embedded \
    ./rpy2/tests/rinterface/test_noinitialization.py

pytest \
    --cov-append \
    --cov-report=xml \
    --cov-report=term \
    --cov=rpy2.rinterface_lib.embedded \
    ./rpy2/tests/rinterface/test_endr.py

for testname in test_threading__initr test_threading_initr_simple; do
  pytest \
      --cov-append \
      --cov-report=xml \
      --cov-report=term \
      --cov=rpy2.rinterface_lib.embedded \
      ./rpy2/tests/rinterface/test_threading.py -k "${testname}"
done

# Added in case the loop above is not updated and is missing tests
pytest \
    --cov-append \
    --cov-report=xml \
    --cov-report=term \
    --cov=rpy2.rinterface_lib.embedded \
    ./rpy2/tests/rinterface/test_threading.py
