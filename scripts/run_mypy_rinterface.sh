#!/bin/bash

mypy rpy2/rinterface.py \
     rpy2/rinterface_lib/*.py \
     rpy2/situation.py \
     --follow-imports=silent
