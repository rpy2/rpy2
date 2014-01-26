#!/bin/bash
#
# Test script for the Continuous Integration server drone.io

# Define the versions of Python that should be tested
PYTHON_VERSIONS="2.7 3.3"

# Define the target Numpy versions
NUMPY_VERSIONS="1.7.1 1.8.0"

DEPS_DIR="deps/"
WHEEL_DIR=$DEPS_DIR"wheelhouse/"
mkdir -p $WHELL_DIR
PIPWITHWHEEL_ARGS=" --download-cache /tmp -w $WHEEL_DIR --use-wheel --find-links=file://$WHEEL_DIR"

# Color escape codes
GREEN='\e[0;32m'
RED='\e[0;31m'
NC='\e[0m'

# Install R and numpy dependencies
# Ensure that we get a recent R
sudo add-apt-repository ppa:marutter/rrutter
sudo apt-get update
sudo apt-get install r-base cython libatlas-dev liblapack-dev gfortran 

# Install ggplot2 r-cran package
export R_LIBS_USER="$HOME/rlibs/"
mkdir -p $R_LIBS_USER
R -e 'install.packages("ggplot2", repos="http://cran.us.r-project.org")'

STATUS=0

# Launch tests for each Python version
for PYVERSION in $PYTHON_VERSIONS; do
  echo -e "${GREEN}Test with Python $PYVERSION ${NC}"

  # Create a new virtualenv
  virtualenv --no-site-packages --python=python$PYVERSION env-$PYVERSION/
  source env-$PYVERSION/bin/activate
  
  # Upgrade pip and install wheel
  pip install setuptools --upgrade
  pip install -I --download-cache /tmp pip
  pip install -I --download-cache /tmp wheel

  for NPVERSION in $NUMPY_VERSIONS; do
    echo -e "${GREEN}    Numpy version $NPVERSION ${NC}"
    # Use the astropy wheels repositories to speedup numpy
    # installation
    pip wheel $PIPWITHWHEEL_ARGS numpy==$NPVERSION
    pip install $PIPWITHWHEEL_ARGS numpy==$NPVERSION
    pip wheel $PIPWITHWHEEL_ARGS pandas
    pip install $PIPWITHWHEEL_ARGS pandas
    pip wheel $PIPWITHWHEEL_ARGS ipython
    pip install $PIPWITHWHEEL_ARGS ipython
  
    # Build rpy2
    rpy2build=`python setup.py sdist | tail -n 1 | grep -Po "removing \\'\K[^\\']*"`
    # Install it (so we also test that the source package is correctly built)
    pip install dist/${rpy2build}.tar.gz
  
    # Launch tests
    python -m rpy2.tests
    if [ $? -eq 0 ]; then
      echo -e "${GREEN}Tests PASSED for Python ${PYVERSION} / Numpy ${NPVERSION} ${NC}"
    else
      STATUS=1
      echo -e "${RED}Tests FAILED for Python ${PYVERSION} / Numpy ${NPVERSION}${NC}"
    fi
  done
done
exit $STATUS
