#!/bin/bash

mypy rpy2/robjects/*.py \
     rpy2/ipython/*.py \
     rpy2/rlike/*.py \
     rpy2/interactive/*.py \
     --follow-imports=silent
