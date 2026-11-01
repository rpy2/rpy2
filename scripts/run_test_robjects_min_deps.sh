#!/bin/bash
set -e
set -x

pytest \
    --cov-report=xml \
    --cov-report=term \
    --cov=rpy2.rlike \
    --cov=rpy2.robjects \
    ./rpy2-robjects/src/rpy2/robjects/tests
