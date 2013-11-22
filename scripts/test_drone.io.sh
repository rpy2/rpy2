#!/bin/bash
#
# Test script for the Continuous Integration server drone.io

# Define the versions of Python that should be tested
PYTHON_VERSIONS="2.7 3.3"

# Define the Numpy version to install
NUMPY_VERSION="1.7.1"

# Color escape codes
GREEN='\e[0;32m'
NC='\e[0m'

# Install R and numpy dependencies
sudo apt-get install r-base python-numpy cython libatlas-dev liblapack-dev gfortran

# Install ggplot2 r-cran package
export R_LIBS_USER="$HOME/rlibs/"
mkdir -p $R_LIBS_USER
R -e 'install.packages("ggplot2", repos="http://cran.us.r-project.org")'

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
      --find-links http://wheels2.astropy.org/ numpy==$NUMPY_VERSION pandas
  
  # Build rpy2
  python setup.py build --build-lib build-$VERSION
  export PYTHONPATH=build-$VERSION/:$PYTHONPATH
  
  # Launch tests
  python -m rpy2.tests
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}Passed tests for Python ${VERSION}${NC}"
  fi
done
