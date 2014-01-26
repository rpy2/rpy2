#!/bin/bash
#
# Test script for the Continuous Integration server drone.io

if [ -z $VERBOSE ] ; then
  VERBOSE=/dev/null;
fi;

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
sudo add-apt-repository ppa:marutter/rrutter > ${VERBOSE}
sudo add-apt-repository ppa:jtaylor/ipython > ${VERBOSE}
sudo add-apt-repository ppa:pythonxy/pythonxy-devel > ${VERBOSE}
sudo apt-get update &> ${VERBOSE}
sudo apt-get -qq -y install r-base cython libatlas-dev liblapack-dev gfortran> ${VERBOSE}
sudo apt-get -qq -y install ipython > ${VERBOSE}
sudo apt-get -qq -y install pandas > ${VERBOSE}

# Install ggplot2 r-cran package
export R_LIBS_USER="$HOME/rlibs/"
mkdir -p $R_LIBS_USER
R --slave -e 'install.packages("ggplot2", repos="http://cran.us.r-project.org")' &> ${VERBOSE}

STATUS=0
summary=()
# Launch tests for each Python version
for PYVERSION in $PYTHON_VERSIONS; do
  echo -e "${GREEN}Test with Python $PYVERSION ${NC}"

  # Create a new virtualenv
  virtualenv --python=python$PYVERSION env-$PYVERSION/ > ${VERBOSE}
  source env-$PYVERSION/bin/activate
  
  # Upgrade pip and install wheel
  pip install setuptools --upgrade > ${VERBOSE}
  pip install -I --download-cache /tmp pip > ${VERBOSE}
  pip install -I --download-cache /tmp wheel > ${VERBOSE}

  for NPVERSION in $NUMPY_VERSIONS; do
    echo -e "${GREEN}    Numpy version $NPVERSION ${NC}"
 
    pip install --use-wheel --find-links http://cache27diy-cpycloud.rhcloud.com/$PYVERSION \
	numpy==$NPVERSION > ${VERBOSE}

    # Build rpy2
    rpy2build=`python setup.py sdist | tail -n 1 | grep -Po "removing \\'\K[^\\']*"`
    # Install it (so we also test that the source package is correctly built)
    pip install dist/${rpy2build}.tar.gz
  
    # Launch tests
    python -m rpy2.tests

    # Success if passing the tests in at least one configuration
    if [ $? -eq 0 ]; then
      msg="${GREEN}Tests PASSED for Python ${PYVERSION} / Numpy ${NPVERSION} ${NC}"
      echo -e $msg
      summary+=($msg) 
      STATUS=1
    else
      msg="${RED}Tests FAILED for Python ${PYVERSION} / Numpy ${NPVERSION} ${NC}"
      echo -e $msg
      summary+=($msg)
      ((STATUS = 0 || $STATUS))
    fi
  done
done
for m in ${summary[@]}; do
  echo -e $m
done
if [ STATUS==1 ]; then
  exit 0;
else
  exit 1;
fi

