#!/usr/bin/env python
import os, os.path, sys, shutil, re, itertools, warnings
import tempfile
import argparse, shlex, subprocess
from collections import namedtuple

from setuptools import setup

if sys.version_info[0] < 3:
    print('rpy2 is no longer supporting Python < 3.'
          'Consider using an older rpy2 release when using an older Python release.')
    sys.exit(1)

pack_name = 'rpy2'
pack_version = __import__('rpy').__version__

package_prefix='.'

R_MIN_VERSION = (3, 3)

def _format_version(x):
    return '.'.join(map(str, x))

    
def _get_r_home(r_bin = 'R'):
    
    if (os.getenv('R_ENVIRON') is not None) or (os.getenv('R_ENVIRON_USER') is not None):
        warnings.warn('The environment variable R_ENVIRON or R_ENVIRON_USER is set.'
                      ' Differences between their settings during build time and run'
                      ' time may lead to issues when using rpy2.')

    try:
        r_home = subprocess.check_output((r_bin, "RHOME"),
                                         universal_newlines=True)
    except:
        msg = "Error: Tried to guess R's HOME but no command '%s' in the PATH." % r_bin
        print(msg)
        sys.exit(1)

    r_home = r_home.split(os.linesep)

    #Twist if 'R RHOME' spits out a warning
    if r_home[0].startswith("WARNING"):
        warnings.warn("R emitting a warning: %s" % r_home[0])
        r_home = r_home[1].rstrip()
    else:
        r_home = r_home[0].rstrip()

    if os.path.exists(os.path.join(r_home, 'Renviron.site')):
        warnings.warn("The optional file '%s' is defined. Modifying it between "
                      "build time and run time may lead to issues when using rpy2." %
                      os.path.join(r_home, 'Renviron.site'))

    return r_home


def cmp_version(x, y):
    if (x[0] < y[0]):
        return -1
    if (x[0] > y[0]):
        return 1
    if (x[0] == y[0]):
        if len(x) == 1 or len(y) == 1:
            return 0
        return cmp_version(x[1:], y[1:])

class RExec(object):
    """ Compilation-related configuration parameters used by R. """

    def __init__(self, r_home):
        if sys.platform == 'win32' and '64 bit' in sys.version:
            r_exec = os.path.join(r_home, 'bin', 'x64', 'R')
        else:
            r_exec = os.path.join(r_home, 'bin', 'R')
        self._r_exec = r_exec
        self._version = None

    @property
    def version(self):
        if self._version is not None:
            return self._version
        output = subprocess.check_output((self._r_exec, '--version'), 
                                         universal_newlines = True)
        if not output:
            # sometimes R output goes to stderr
            output = subprocess.check_output((self._r_exec, '--version'), 
                                         stderr = subprocess.STDOUT,
                                         universal_newlines = True)
        output = iter(output.split('\n'))
        rversion = next(output)
        #Twist if 'R --version' spits out a warning
        if rversion.startswith('WARNING'):
            warnings.warn('R emitting a warning: %s' % rversion)
            rversion = next(output)
        print(rversion)
        m = re.match('^R ([^ ]+) ([^ ]+) .+$', rversion)
        if m is None:
            warnings.warn("Unable to extract R's version number from the string: '%s'" % rversion)
            # return dummy version 0.0
            rversion = [0, 0]
        else:
            rversion = m.groups()[1]
            if m.groups()[0] == 'version':
                rversion = [int(x) for x in rversion.split('.')]
            else:
                rversion = ['development', '']
        self._version = rversion
        return self._version

    def cmd_config(self, about, allow_empty=False):
        cmd = (self._r_exec, 'CMD', 'config', about)
        print(subprocess.list2cmdline(cmd))
        output = subprocess.check_output(cmd,
                                         universal_newlines = True)
        output = output.split(os.linesep)
        #Twist if 'R RHOME' spits out a warning
        if output[0].startswith("WARNING"):
            warnings.warn('R emitting a warning: %s' % output[0])
            output = output[1:]
        return output


LONG_DESCRIPTION = """
Python interface to the R language.

`rpy2` is running an embedded R, providing access to it from Python 
using R's own C-API through either:

- a high-level interface making R functions an objects just like Python
  functions and providing a seamless conversion to numpy and pandas data 
  structures
- a low-level interface closer to the C-API

It is also providing features for when working with jupyter notebooks or
ipython.
"""

if __name__ == '__main__':
    pack_dir = {pack_name: os.path.join(package_prefix, 'rpy')}

    if sys.version_info[0] == 2 and sys.version_info[1] < 7:
        print('rpy2 requires at least Python Version 2.7 '
              '(with Python 3.5 or later recommended).')
        sys.exit(1)
        
    requires = ['pytest', 'jinja2', 'simplegeneric']

    if sys.version_info[0] < 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 4):
        requires.append('singledispatch')
    
    setup(
        name = pack_name,
        version = pack_version,
        description = 'Python interface to the R language (embedded R)',
        long_description = LONG_DESCRIPTION,
        url = 'https://rpy2.bitbucket.io',
        license = 'GPLv2+',
        author = 'Laurent Gautier',
        author_email = 'lgautier@gmail.com',
        requires = requires,
        install_requires = requires + ['cffi>=1.0.0'],
        setup_requires = ['cffi>=1.0.0'],
        cffi_modules = ['rpy/_rinterface_cffi_build.py:ffibuilder'],
        package_dir = pack_dir,
        packages = [pack_name,
                    pack_name + '.rlike',
                    pack_name + '.rinterface_lib',
                    pack_name + '.robjects',
                    pack_name + '.robjects.lib',
                    pack_name + '.interactive',
                    pack_name + '.ipython',
                    ],
        classifiers = ['Programming Language :: Python',
                       'Programming Language :: Python :: 3',
                       'Programming Language :: Python :: 3.5',
                       'Programming Language :: Python :: 3.6',
                       'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
                       'Intended Audience :: Developers',
                       'Intended Audience :: Science/Research',
                       'Development Status :: 5 - Production/Stable'
                       ],
        package_data = {
            'rpy2': ['images/*.png', ],
            'rpy2': ['doc/source/rpy2_logo.png', ]}
        )

