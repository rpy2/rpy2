#!/bin/bash

MYPYPATH=src mypy \
	     --namespace-packages \
	     --explicit-package-bases \
	     --exclude src/rpy2/rinterface/tests \
	     --exclude src/rpy2/_rinterface_cffi_build.py \
	     --exclude setup.py \
	     .
