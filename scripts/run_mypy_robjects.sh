#!/bin/bash

mypy src/rpy2/robjects/*.py \
     src/rpy2/ipython/*.py \
     src/rpy2/rlike/*.py \
     src/rpy2/interactive/*.py \
     --follow-imports=silent
