#!/bin/bash

mypy --install-types \
     rpy2/rinterface.py \
     rpy2/rinterface_lib/*.py \
     rpy2/robjects/*.py \
     rpy2/ipython/*.py \
     rpy2/rlike/*.py \
     rpy2/situation.py \
     rpy2/interactive/*.py \
     --follow-imports=silent
