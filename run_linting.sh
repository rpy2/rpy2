#!/bin/bash

flake8 \
    rpy/ipython/ \
    rpy/rinterface.py \
    rpy/rinterface_lib/ \
    rpy/rlike/functional.py \
    rpy/rlike/indexing.py \
    rpy/robjects/c*.py \
    rpy/robjects/environment.py \
    rpy/robjects/language.py \
    rpy/robjects/lib \
    rpy/robjects/methods.py \
    rpy/robjects/numpy2ri.py \
    rpy/robjects/packages.py \
    rpy/robjects/packages_utils.py \
    rpy/robjects/pandas2ri.py \
    rpy/robjects/vectors.py
