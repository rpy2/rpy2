#!/bin/bash

mypy src/rpy2/rinterface/__init__.py \
     src/rpy2/rinterface_lib/*.py \
     src/rpy2/situation/__init__.py \
     --follow-imports=silent
