#!/usr/bin/env python
import sys
if ((sys.version_info[0] < 3) or
    (sys.version_info[0] == 3 and sys.version_info[1] < 9)):
    print('rpy2 is no longer supporting Python < 3.9.'
          'Consider using an older rpy2 release when using an '
          'older Python release.')
    sys.exit(1)

import enum
import importlib
import os
import shutil
import subprocess
import tempfile
import typing
import warnings

from setuptools import dist, Extension, find_namespace_packages, setup
from setuptools._distutils.ccompiler import new_compiler
from setuptools._distutils.sysconfig import customize_compiler

import setuptools.command.build
import setuptools.command.build_ext
import setuptools.command.install

link_args = ['-static-libgcc',
             '-static-libstdc++',
             '-Wl,-Bstatic,--whole-archive',
             '-lwinpthread',
             '-Wl,--no-whole-archive']


class build_ext(setuptools.command.build_ext.build_ext):
    def build_extensions(self):
        if self.compiler.compiler_type == 'mingw32':
            for e in self.extensions:
                e.extra_link_args = link_args
        super().build_extensions()


# spec = importlib.util.spec_from_file_location('rpy2', './rpy2/__init__.py')
# rpy2 = importlib.util.module_from_spec(spec)
# sys.modules['rpy2'] = rpy2
# spec.loader.exec_module(rpy2)

spec = importlib.util.spec_from_file_location('situation', 'src/rpy2/situation/__init__.py')
situation = importlib.util.module_from_spec(spec)
sys.modules['situation'] = situation
spec.loader.exec_module(situation)


PACKAGE_NAME = 'rpy2'
package_prefix='src'

R_MIN_VERSION = (3, 5)

def cmp_version(x, y):
    if (x[0] < y[0]):
        return -1
    if (x[0] > y[0]):
        return 1
    if (x[0] == y[0]):
        if len(x) == 1 or len(y) == 1:
            return 0
        return cmp_version(x[1:], y[1:])


def _distutils_error_classes(name):
    """Collect a distutils error class from every module copy exposing it.

    setuptools' distutils hack can expose the distutils error classes
    through two distinct module objects (e.g.
    ``distutils.compilers.C.errors`` vs
    ``setuptools._distutils.compilers.C.errors``). The compiler may raise an
    instance from one copy while a single import resolves to the other, so
    we gather the class from both locations and match against all of them.
    """
    classes = []
    for module_name in ('distutils.errors', 'setuptools._distutils.errors'):
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue
        klass = getattr(module, name, None)
        if klass is not None:
            classes.append(klass)
    return tuple(classes)


_COMPILE_ERRORS = _distutils_error_classes('CCompilerError')
_NO_COMPILER_ERRORS = _distutils_error_classes('DistutilsExecError')
_PLATFORM_ERRORS = _distutils_error_classes('DistutilsPlatformError')
_TOOLCHAIN_ERRORS = _COMPILE_ERRORS + _NO_COMPILER_ERRORS + _PLATFORM_ERRORS


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
        # On Windows the pre-build phase (get_requires_for_build_wheel) runs
        # with the system default compiler (MSVC) even when the actual build
        # uses MinGW.  Flags from "R CMD config --ldflags" are MinGW-style
        # (e.g. -lm, -lR pointing to bin/x64) and are not valid for MSVC.
        # Only verify that a C compiler is available; the actual R linkage
        # will be exercised during the real MinGW build.
        libraries = []
        library_dirs = []
        include_dirs = []
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
    except _TOOLCHAIN_ERRORS as e:
        # A recognized toolchain failure: the target system is missing the
        # R headers, a usable compiler, or a supported platform. In ANY mode
        # this lets the build fall back to ABI. Any *other* exception is
        # treated as a real bug in the build process and left to propagate,
        # so we still notice when the build itself is broken.
        if isinstance(e, _NO_COMPILER_ERRORS):
            status = COMPILATION_STATUS.NO_COMPILER
        elif isinstance(e, _PLATFORM_ERRORS):
            status = COMPILATION_STATUS.PLATFORM_ERROR
        else:
            status = COMPILATION_STATUS.COMPILE_ERROR
        print(e)
    else:
        status = COMPILATION_STATUS.OK
    shutil.rmtree(tmp_dir)
    return status


def get_r_c_extension_status(r_home: typing.Optional[str],
                             force_ok: bool = False):
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
    if force_ok:
        status = COMPILATION_STATUS.OK
    else:
        status = get_c_extension_status(libraries=c_ext.libraries,
                                        include_dirs=c_ext.include_dirs,
                                        library_dirs=c_ext.library_dirs)
    return status


class install(setuptools.command.install.install):

    def run(self):
        if r_home:
            print(
                'LD_LIBRARY_PATH in R: {}'.format(
                    situation.r_ld_library_path_from_subprocess(r_home)
                )
            )
        super().run()


r_home = situation.get_r_home()
cffi_mode = situation.get_cffi_mode()
c_extension_status = get_r_c_extension_status(
    r_home,
    force_ok=os.environ.get('RPY2_API_FORCE') == 'True'
)
ext_modules = []

_CFFI_BUILD_PATH='src/rpy2/rinterface_lib/_rinterface_cffi_build.py'

if cffi_mode == situation.CFFI_MODE.ABI:
    cffi_modules = [f'{_CFFI_BUILD_PATH}:ffibuilder_abi']
elif cffi_mode == situation.CFFI_MODE.API:
    if c_extension_status != COMPILATION_STATUS.OK:
        print('API mode requested but %s' % c_extension_status.value)
        sys.exit(1)
    cffi_modules = [f'{_CFFI_BUILD_PATH}:ffibuilder_api']
    ext_modules = [
        Extension('rpy2.rinterface_lib._bufferprotocol',
                  ['src/rpy2/rinterface_lib/_bufferprotocol.c'])
    ]
elif cffi_mode == situation.CFFI_MODE.BOTH:
    if c_extension_status != COMPILATION_STATUS.OK:
        print('API mode requested but %s' % c_extension_status.value)
        sys.exit(1)
    cffi_modules = [f'{_CFFI_BUILD_PATH}:ffibuilder_abi',
                    f'{_CFFI_BUILD_PATH}:ffibuilder_api']
elif cffi_mode == situation.CFFI_MODE.ANY:
    # default interface
    cffi_modules = [f'{_CFFI_BUILD_PATH}:ffibuilder_abi']
    if c_extension_status == COMPILATION_STATUS.OK:
        cffi_modules.append(f'{_CFFI_BUILD_PATH}:ffibuilder_api')
        ext_modules = [
            Extension('rpy2.rinterface_lib._bufferprotocol',
                      ['src/rpy2/rinterface_lib/_bufferprotocol.c'])
        ]
else:
    # This should never happen.
    raise ValueError('Invalid value for cffi_mode')


class build(setuptools.command.build.build):

    def run(self):
        print('cffi mode: %s' % cffi_mode)

        super().run()

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

setup(
    cffi_modules=cffi_modules,
    ext_modules=ext_modules,
    cmdclass={'build': build, 'build_ext': build_ext},
    zip_safe=False
)
