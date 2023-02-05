#!/usr/bin/env python
import sys
if ((sys.version_info[0] < 3) or
    (sys.version_info[0] == 3 and sys.version_info[1] < 7)):
    print('rpy2 is no longer supporting Python < 3.7.'
          'Consider using an older rpy2 release when using an '
          'older Python release.')
    sys.exit(1)

import enum
import os
import shutil
import subprocess
import tempfile
import warnings

from setuptools import setup, Extension, dist
from distutils.ccompiler import new_compiler
from distutils.sysconfig import customize_compiler
from distutils.errors import CCompilerError, DistutilsExecError, DistutilsPlatformError

from distutils.command.build import build as du_build

# from rpy2 import situation
import importlib

# spec = importlib.util.spec_from_file_location('rpy2', './rpy2/__init__.py')
# rpy2 = importlib.util.module_from_spec(spec)
# sys.modules['rpy2'] = rpy2
# spec.loader.exec_module(rpy2)

spec = importlib.util.spec_from_file_location('situation', './rpy2/situation.py')
situation = importlib.util.module_from_spec(spec)
sys.modules['situation'] = situation
spec.loader.exec_module(situation)


PACKAGE_NAME = 'rpy2'
package_prefix='.'

R_MIN_VERSION = (3, 3)

def cmp_version(x, y):
    if (x[0] < y[0]):
        return -1
    if (x[0] > y[0]):
        return 1
    if (x[0] == y[0]):
        if len(x) == 1 or len(y) == 1:
            return 0
        return cmp_version(x[1:], y[1:])


class COMPILATION_STATUS(enum.Enum):
    COMPILE_ERROR=('unable to compile R C extensions - missing headers '
                   'or R not compiled as a library ?')
    NO_COMPILER=('unable to compile sqlite3 C extensions - '
                 'no c compiler?')
    PLATFORM_ERROR=('unable to compile R C extensions - platform error')
    OK = None
    NO_R='No R in the PATH, or R_HOME defined.'
    RFLAGS_ERROR='Unable to get R compilation flags'


def get_c_extension_status(libraries=['R'], include_dirs=None,
                           library_dirs=None):
    if os.name == 'nt':
        c_code = ('int main(int argc, char **argv) { return 0; }')
    else:
        c_code = ('#include <Rinterface.h>\n\n'
                  'int main(int argc, char **argv) { return 0; }')
    tmp_dir = tempfile.mkdtemp(prefix='tmp_pw_r_')
    bin_file = os.path.join(tmp_dir, 'test_pw_r')
    src_file = bin_file + '.c'
    with open(src_file, 'w') as fh:
        fh.write(c_code)

    compiler = new_compiler()
    customize_compiler(compiler)
    try:
        compiler.link_executable(
            compiler.compile([src_file], output_dir=tmp_dir,
                             include_dirs=include_dirs),
            bin_file,
            libraries=libraries,
            library_dirs=library_dirs)
    except CCompilerError as cce:
        status = COMPILATION_STATUS.COMPILE_ERROR
        print(cce)
    except DistutilsExecError as dee:
        status = COMPILATION_STATUS.NO_COMPILER
        print(dee)
    except DistutilsPlatformError as dpe:
        status = COMPILATION_STATUS.PLATFORM_ERROR
        print(dpe)
    else:
        status = COMPILATION_STATUS.OK
    shutil.rmtree(tmp_dir)
    return status


def get_r_c_extension_status():

    r_home = situation.get_r_home()
    if r_home is None:
        return COMPILATION_STATUS.NO_R
    c_ext = situation.CExtensionOptions()
    try:
        c_ext.add_lib(
            *situation.get_r_flags(r_home, '--ldflags')
        )
        c_ext.add_include(
            *situation.get_r_flags(r_home, '--cppflags')
        )
    except subprocess.CalledProcessError as cpe:
        warnings.warn(str(cpe))
        return COMPILATION_STATUS.RFLAGS_ERROR
    status = get_c_extension_status(libraries=c_ext.libraries,
                                    include_dirs=c_ext.include_dirs,
                                    library_dirs=c_ext.library_dirs)
    return status

cffi_mode = situation.get_cffi_mode()
c_extension_status = get_r_c_extension_status()
ext_modules = []
if cffi_mode == situation.CFFI_MODE.ABI:
    cffi_modules = ['rpy2/_rinterface_cffi_build.py:ffibuilder_abi']
elif cffi_mode == situation.CFFI_MODE.API:
    if c_extension_status != COMPILATION_STATUS.OK:
        print('API mode requested but %s' % c_extension_status.value)
        sys.exit(1)
    cffi_modules = ['rpy2/_rinterface_cffi_build.py:ffibuilder_api']
    ext_modules = [
        Extension('rpy2.rinterface_lib._bufferprotocol',
                  ['rpy2/rinterface_lib/_bufferprotocol.c'])
    ]
elif cffi_mode == situation.CFFI_MODE.BOTH:
    if c_extension_status != COMPILATION_STATUS.OK:
        print('API mode requested but %s' % c_extension_status.value)
        sys.exit(1)
    cffi_modules = ['rpy2/_rinterface_cffi_build.py:ffibuilder_abi',
                    'rpy2/_rinterface_cffi_build.py:ffibuilder_api']
elif cffi_mode == situation.CFFI_MODE.ANY:
    # default interface
    cffi_modules = ['rpy2/_rinterface_cffi_build.py:ffibuilder_abi']
    if c_extension_status == COMPILATION_STATUS.OK:
        cffi_modules.append('rpy2/_rinterface_cffi_build.py:ffibuilder_api')
        ext_modules = [
            Extension('rpy2.rinterface_lib._bufferprotocol',
                      ['rpy2/rinterface_lib/_bufferprotocol.c'])
        ]
else:
    # This should never happen.
    raise ValueError('Invalid value for cffi_mode')


class build(du_build):

    def run(self):
        print('cffi mode: %s' % cffi_mode)

        du_build.run(self)

        print('---')
        print(cffi_mode)
        if cffi_mode in (situation.CFFI_MODE.ABI,
                         situation.CFFI_MODE.BOTH,
                         situation.CFFI_MODE.ANY):
            print('ABI mode interface built.')
        if cffi_mode in (situation.CFFI_MODE.API,
                         situation.CFFI_MODE.BOTH):
            print('API mode interface built.')
        if cffi_mode == situation.CFFI_MODE.ANY:
            if c_extension_status == COMPILATION_STATUS.OK:
                print('API mode interface built.')
            else:
                print('API mode interface not built because: %s' % c_extension_status)
        print('To change the API/ABI build mode, set or modify the environment '
              'variable RPY2_CFFI_MODE.')


pack_dir = {PACKAGE_NAME: os.path.join(package_prefix, 'rpy2')}
with open('README.md') as fh:
    long_description = fh.read()

setup(
    cffi_modules=cffi_modules,
    ext_modules=ext_modules,
    cmdclass=dict(build=build),
    long_description=long_description, 
    # List of pacakges moved to project.toml.
    # TODO: package_data should be be moved to project.toml when setuptools
    # supports it (see note in project.toml).
    package_data={'rpy2': ['rinterface_lib/R_API.h',
                            'rinterface_lib/R_API_eventloop.h',
                            'rinterface_lib/R_API_eventloop.c',
                            'rinterface_lib/RPY2.h',
                            'rinterface_lib/_bufferprotocol.c',
                            'py.typed']},
    zip_safe=False
)
