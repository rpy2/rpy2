# Python -> R bridge

[![pypi](https://img.shields.io/pypi/v/rpy2.svg?style=flat-square)](https://pypi.python.org/pypi/rpy2)
[![Codecov](https://codecov.io/gh/rpy2/rpy2/branch/master/graph/badge.svg)](https://codecov.io/gh/rpy2/rpy2)
[![GH Actions](https://github.com/rpy2/rpy2/workflows/Python%20package/badge.svg)](https://github.com/rpy2/rpy2/actions?query=workflow%3A%22Python+package%22)

![PyPI - Downloads](https://img.shields.io/pypi/dm/rpy2?style=flat&label=pypi)
![Conda Downloads](https://img.shields.io/conda/dn/conda-forge/rpy2?label=conda-forge)

The project's webpage is here: https://rpy2.github.io/


# Installation

Released versions can be installed from a package repository (default
being pypi) using pip:

```bash
pip install rpy2
```

The package has optional depencies providing
specific functionalities not otherwise required to use the rest of rpy2.

For example, to be able to run the unit tests:
```bash
pip install 'rpy2[test]'
```

To install all optional dependencies (numpy, pandas, ipython), use:

```bash
pip install 'rpy2[all]'
```

## Installation for rpy2 developers

If a developer, the package can be installed from its source tree.
`rpy2` is a namespace package with its consituting parts in different
"sub-packages".

To install from the source tree, just enter:

```bash
pip install ./rpy2-rinterface/ ./rpy2-robjects/ .
```

Various optional dependencies can be specified through dependency groups.
For example:

```bash
pip install ./rpy2-rinterface'[all]' ./rpy2-robjects'[all]' '.[all]'
```

`rpy2-rinterface` contains the binding to R's C API. Building from
source require a compilation toolchain / developper tools installed,
and you will have to figure out how to have them installed on your
system by yourself. The CI pipeline builds binary wheels for Linux,
MacOS, and Windows. Watching how things are set up there is pretty
much all documentation from the package maintainers on the matter.


## Issues loading shared C libraries

Whenever R is in not installed in a system location, the system might not
know where to find the R shared library.

If `R` is in the `PATH`, that is entering `R` on the command line successfully starts
an R terminal, but rpy2 does not work because of missing C libraries, try the following
before starting Python:


```bash
export LD_LIBRARY_PATH="$(python -m rpy2.situation LD_LIBRARY_PATH)":${LD_LIBRARY_PATH}
```


# Documentation

Documentation is available either in the source tree (`doc/`),
or [online](https://rpy2.github.io/doc.html).


## Testing

`rpy2` uses `pytest`, with the plugin `pytest-cov` for code coverage. To
test the package from the source tree, either to check and installation
on your system or before submitting a pull request, do:

```bash
pytest rpy2-rinterface/ rpy2-robjects/
```

For code coverage, do:

```bash
pytest --cov=rpy2.rinterface_lib \
       --cov=rpy2.rinterface \
       --cov=rpy2.ipython \
       --cov=rpy2.robject \
       rpy2-rinterface/ rpy2-robjects/
```

For more options, such as how to run specify tests, please refer to the `pytest`
documentation.


# License

RPy2 can be used under the terms of the GNU
General Public License Version 2 or later (see the file
gpl-2.0.txt). This is the very same license R itself is released under.
