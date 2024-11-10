#!/bin/bash

flake8 \
    --max-line-length 90 \
    rpy2/situation.py \
    rpy2/_rinterface_cffi_build.py \
    rpy2/rinterface.py \
    rpy2/rinterface_lib/
