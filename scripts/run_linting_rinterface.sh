#!/bin/bash

flake8 \
    --max-line-length 90 \
    src/rpy2/situation.py \
    src/rpy2/_rinterface_cffi_build.py \
    src/rpy2/rinterface.py \
    src/rpy2/rinterface_lib/
