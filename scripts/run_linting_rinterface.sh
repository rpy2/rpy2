#!/bin/bash

flake8 \
    --max-line-length 90 \
    src/rpy2/rlike/functional.py \
    src/rpy2/rlike/indexing.py \
    src/rpy2/situation/__init__.py \
    src/rpy2/rinterface/__init__.py \
    src/rpy2/rinterface_lib/
