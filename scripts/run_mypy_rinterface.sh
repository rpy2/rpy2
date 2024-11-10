#!/bin/bash

mypy src/rpy2/rinterface.py \
     src/rpy2/rinterface_lib/*.py \
     src/rpy2/situation.py \
     --follow-imports=silent
