#!/bin/bash

pwd

ls

ls src/rpy2

flake8 \
    --max-line-length 90 \
    src/rpy2/ipython/ \
    src/rpy2/robjects/c*.py \
    src/rpy2/robjects/environments.py \
    src/rpy2/robjects/functions.py \
    src/rpy2/robjects/help.py \
    src/rpy2/robjects/language.py \
    src/rpy2/robjects/lib \
    src/rpy2/robjects/methods.py \
    src/rpy2/robjects/numpy2ri.py \
    src/rpy2/robjects/robject.py \
    src/rpy2/robjects/packages.py \
    src/rpy2/robjects/packages_utils.py \
    src/rpy2/robjects/pandas2ri.py \
    src/rpy2/robjects/vectors.py
