#!/bin/bash

MYPYPATH=src mypy \
	     --namespace-packages \
	     --explicit-package-bases \
	     --exclude src/rpy2/robjects/tests \
	     --exclude build/ \
	     .
