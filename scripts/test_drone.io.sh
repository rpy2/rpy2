#!/bin/bash
#
# Test script for the Continuous Integration server drone.io

# Define the versions of Python that should be tested
PYTHON_VERSIONS="2.7 3.3"

# Define the Numpy version to install
NUMPY_VERSION="1.7.1"

# Color escape codes
GREEN='\e[0;32m'
RED='\e[0;31m'
NC='\e[0m'

# Install R and numpy dependencies
# Ensure that we get a recent R
sudo add-apt-repository ppa:marutter/rruter
sudo apt-get install r-base cython libatlas-dev liblapack-dev gfortran 

# Install ggplot2 r-cran package
export R_LIBS_USER="$HOME/rlibs/"
mkdir -p $R_LIBS_USER
R -e 'install.packages("ggplot2", repos="http://cran.us.r-project.org")'

STATUS=0

# Launch tests for each Python version
for VERSION in $PYTHON_VERSIONS; do
  echo -e "${GREEN}Test with Python $VERSION ${NC}"

  # Create a new virtualenv
  virtualenv --no-site-packages --python=python$VERSION env-$VERSION/
  source env-$VERSION/bin/activate
  
  # Upgrade pip and install wheel
  pip install setuptools --upgrade
  pip install pip --upgrade
  pip install wheel
  
  # Use the astropy wheels repositories to speedup numpy
  # installation
  pip install --use-wheel --find-links http://wheels.astropy.org/ \
      --find-links http://wheels2.astropy.org/ \
      numpy==$NUMPY_VERSION pandas ipython
  
  # Build rpy2
  python setup.py sdist
  # Install it (so we also test that the source package is correctly built)
  pip install dist/rpy2-2.4.0.tar.gz
  
  # Launch tests
  python -m rpy2.tests
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}Tests PASSED for Python ${VERSION}${NC}"
  else
    STATUS=1
    echo -e "${RED}Tests FAILED for Python ${VERSION}${NC}"
  fi
done
exit $STATUS
