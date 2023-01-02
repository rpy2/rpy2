#!/bin/bash

flake8 \
    --max-line-length 90 \
    rpy2/ipython/ \
    rpy2/situation.py \
    rpy2/_rinterface_cffi_build.py \
    rpy2/rinterface.py \
    rpy2/rinterface_lib/ \
    rpy2/rlike/functional.py \
    rpy2/rlike/indexing.py \
    rpy2/robjects/c*.py \
    rpy2/robjects/environments.py \
    rpy2/robjects/functions.py \
    rpy2/robjects/help.py \
    rpy2/robjects/language.py \
    rpy2/robjects/lib \
    rpy2/robjects/methods.py \
    rpy2/robjects/numpy2ri.py \
    rpy2/robjects/robject.py \
    rpy2/robjects/packages.py \
    rpy2/robjects/packages_utils.py \
    rpy2/robjects/pandas2ri.py \
    rpy2/robjects/vectors.py
