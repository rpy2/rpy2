#!/bin/bash

MYPYPATH=src mypy \
	     --namespace-packages \
	     --explicit-package-bases \
	     --exclude src/rpy2/rinterface/tests \
	     --exclude src/rpy2/rinterface_lib/_rinterface_cffi_build.py \
	     --exclude build \
	     --exclude setup.py \
	     .
