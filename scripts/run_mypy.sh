#!/bin/bash

mypy rpy2/rinterface.py \
     rpy2/rinterface_lib/*.py \
     rpy2/robjects/*.py \
     rpy2/ipython/*.py \
     rpy2/rlike/*.py \
     rpy2/situation.py \
     rpy2/interactive/*.py \
     --exclude '*_rinterface_cffi_abi.py'
