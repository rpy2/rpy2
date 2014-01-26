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

# Install R, ipython, and pandas
# Ensure that we get recent versions
sudo add-apt-repository ppa:marutter/rrutter
sudo add-apt-repository ppa:jtaylor/ipython
sudo add-apt-repository ppa:pythonxy/pythonxy-devel
sudo apt-get update
sudo apt-get install r-base cython libatlas-dev liblapack-dev gfortran
sudo apt-get install ipython
sudo apt-get install pandas

# Install ggplot2 r-cran package
export R_LIBS_USER="$HOME/rlibs/"
mkdir -p $R_LIBS_USER
R -e 'install.packages("ggplot2", repos="http://cran.us.r-project.org")'

STATUS=0

# Launch tests for each Python version
for PYVERSION in $PYTHON_VERSIONS; do
  echo -e "${GREEN}Test with Python $PYVERSION ${NC}"

  # Create a new virtualenv
  virtualenv --python=python$PYVERSION env-$PYVERSION/
  source env-$PYVERSION/bin/activate
  
  # Upgrade pip and install wheel
  pip install setuptools --upgrade
  pip install -I --download-cache /tmp pip
  pip install -I --download-cache /tmp wheel

  for NPVERSION in $NUMPY_VERSIONS; do
    echo -e "${GREEN}    Numpy version $NPVERSION ${NC}"
 
    pip install --use-wheel --find-links http://cache27diy-cpycloud.rhcloud.com/$PYVERSION \
	numpy==$NPVERSION

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
