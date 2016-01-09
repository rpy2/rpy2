#!/bin/bash
#
# Test script for the Continuous Integration server drone.io

LOGFILE=`pwd`/'ci.log'

# Define the versions of Python that should be tested
#PYTHON_VERSIONS="2.7 3.3 3.4"
#PYTHON_VERSIONS="3.4"
PYTHON_VERSIONS="2.7 3.4 3.5"

# Define the target Numpy versions
NUMPY_VERSIONS="1.10.4"

# Settings to install python packages as wheels
DEPS_DIR="deps/"
WHEEL_DIR=${DEPS_DIR}"wheelhouse/"
mkdir -p ${WHEEL_DIR}
PIPWITHWHEEL_ARGS=" -w $WHEEL_DIR --use-wheel --find-links=file://$WHEEL_DIR"

# Color escape codes
GREEN='\e[0;32m'
RED='\e[0;31m'
NC='\e[0m'

echo "CI on drone.io" > ${LOGFILE}

# make debconf silent
export DEBIAN_FRONTEND=noninteractive


# Install R, ipython, and pandas
# Ensure that we get recent versions
echo -n "Installing packages with APT..."
sudo add-apt-repository ppa:marutter/rrutter >> ${LOGFILE}
sudo add-apt-repository ppa:marutter/c2d4u >> ${LOGFILE}
#sudo add-apt-repository ppa:jtaylor/ipython >> ${LOGFILE}
#sudo add-apt-repository ppa:pythonxy/pythonxy-devel > ${LOGFILE}
sudo apt-get -y update &>> ${LOGFILE}
sudo apt-get -qq -y install r-base \
                            r-cran-ggplot2 \
	                    libatlas-dev \
	                    libatlas3gf-base \
		            liblapack-dev \
		            gfortran &>> ${LOGFILE};

#sudo apt-get -qq -y install pandas >> ${LOGFILE}
echo "[done]"

# Install r-cran packages ggplot2 and Cairo
echo -n "Installing R packages..."
export R_LIBS_USER="$HOME/rlibs/"
mkdir -p $R_LIBS_USER
R --slave -e 'install.packages(c("Cairo"), repos="http://cran.us.r-project.org")' &>> ${LOGFILE}
echo "[done]"

STATUS=0
summary=()
# Launch tests for each Python version
for PYVERSION in $PYTHON_VERSIONS; do
  echo -e "${GREEN}Test with Python $PYVERSION ${NC}"

  sudo apt-get -qq -y install python$PYVERSION python${PYVERSION}-dev
  # Create a new virtualenv
  virtualenv --python=python$PYVERSION env-$PYVERSION/ >> ${LOGFILE}
  source env-$PYVERSION/bin/activate
  
  # Upgrade pip and install wheel
  pip install setuptools --upgrade >> ${LOGFILE}
  pip install -I pip >> ${LOGFILE}
  pip install -I wheel >> ${LOGFILE}

  for NPVERSION in $NUMPY_VERSIONS; do
    echo -e "${GREEN}    Numpy version $NPVERSION ${NC}"

    echo "Installing packages:"
    for package in numpy==$NPVERSION pandas ipython; do
	echo "    $package";
	pip install --use-wheel \
	    --find-links https://cache27diy-cpycloud.rhcloud.com/$PYVERSION \
	    $package >> ${LOGFILE};
    done
    if [ '2.7' = $PYVERSION ]; then
	echo "    singledispatch"
	pip install singledispatch >> ${LOGFILE}
    fi;
    if [ '3.3' = $PYVERSION ]; then
	echo "    singledispatch"
	pip install singledispatch >> ${LOGFILE}
    fi;
    echo '.'
    #pip install --use-wheel --find-links https://cache27diy-cpycloud.rhcloud.com/$PYVERSION cython

    echo "Building rpy2"
    # Build rpy2
    rpy2build=`python setup.py sdist | tail -n 1 | grep -Po "removing \\'\K[^\\']*"`
    # Install it (so we also test that the source package is correctly built)
    pip install dist/${rpy2build}.tar.gz

    #DEBUG
    #python -c 'import rpy2.ipython'
    # Launch tests
    python -m rpy2.tests

    # Success if passing the tests in at least one configuration
    if [ $? -eq 0 ]; then
      msg="${GREEN}Tests PASSED for Python ${PYVERSION} / Numpy ${NPVERSION} ${NC}"
      echo -e $msg
      summary+=("$msg") 
      STATUS=1
    else
      msg="${RED}Tests FAILED for Python ${PYVERSION} / Numpy ${NPVERSION} ${NC}"
      echo -e $msg
      summary+=("$msg")
      ((STATUS = 0 || $STATUS))
    fi
  done
done
echo '=========='
for ((i = 0; i < ${#summary[@]}; i++))
do
  echo -e ${summary[$i]}
done
if [ $STATUS -eq 1 ]; then
  exit 0;
else
  exit 1;
fi

