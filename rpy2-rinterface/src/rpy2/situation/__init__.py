"""
This module is currently primarily intended to be used as a script.
It will print information about the rpy2's environment (Python version,
R version, rpy2 version, etc...).
"""

import argparse
import enum
import logging
import os
import shlex
import subprocess
import sys
from typing import Optional
import warnings

logger = logging.getLogger(__name__)

if sys.maxsize > 2**32:
    r_version_folder = 'x64'
else:
    r_version_folder = 'i386'

ENVVAR_CFFI_TYPE: str = 'RPY2_CFFI_MODE'


class CFFI_MODE(enum.Enum):
    API = 'API'
    ABI = 'ABI'
    BOTH = 'BOTH'
    ANY = 'ANY'


def get_cffi_mode(default=CFFI_MODE.ANY):
    cffi_mode = os.environ.get(ENVVAR_CFFI_TYPE, '')
    res = default
    for m in (CFFI_MODE.API, CFFI_MODE.ABI,
              CFFI_MODE.BOTH, CFFI_MODE.ANY):
        if cffi_mode.upper() == m.value:
            res = m
    logger.info(f'cffi mode is {m}')
    return res


def assert_python_version():
    if not (sys.version_info[0] >= 3 and sys.version_info[1] >= 7):
        msg = 'Python >=3.3 is required to run rpy2'
        logger.error(msg)
        raise RuntimeError(msg)


def r_version_from_subprocess():
    cmd = ('R', '--version')
    logger.debug('Looking for R version with: {}'.format(' '.join(cmd)))
    try:
        tmp = subprocess.check_output(cmd,
                                      stderr=subprocess.STDOUT)
    except Exception as e:  # FileNotFoundError, WindowsError, etc
        logger.error(f'Unable to determine the R version: {e}')
        return None
    r_version = tmp.decode('ascii', 'ignore').split(os.linesep)
    if r_version[0].startswith('WARNING'):
        r_version = r_version[1]
    else:
        r_version = r_version[0].strip()
    logger.info(f'R version found: {r_version}')
    return r_version


def r_home_from_subprocess() -> Optional[str]:
    """Return the R home directory from calling 'R RHOME'."""
    cmd = ('R', 'RHOME')
    logger.debug('Looking for R home with: {}'.format(' '.join(cmd)))
    tmp = subprocess.check_output(cmd, universal_newlines=True)
    # may raise FileNotFoundError, WindowsError, etc
    r_home = tmp.split(os.linesep)
    if r_home[0].startswith('WARNING'):
        res = r_home[1]
    else:
        res = r_home[0].strip()
    return res


# TODO: move all Windows all code into an os-specific module ?
def r_home_from_registry() -> Optional[str]:
    """Return the R home directory from the Windows Registry."""
    from packaging.version import Version
    try:
        import winreg  # type: ignore
    except ImportError:
        import _winreg as winreg  # type: ignore
    # There are two possible locations for RHOME in the registry
    # We prefer the user installation (which the user has more control
    # over). Thus, HKEY_CURRENT_USER is the first item in the list and
    # the for-loop breaks at the first hit.
    for w_hkey in [
            winreg.HKEY_CURRENT_USER,  # type: ignore
            winreg.HKEY_LOCAL_MACHINE  # type: ignore
    ]:
        try:
            with winreg.OpenKeyEx(  # type:ignore
                    w_hkey, 'Software\\R-core\\R'
            ) as hkey:

                # >v4.x.x: grab the highest version installed
                def get_version(i):
                    try:
                        return Version(winreg.EnumKey(hkey, i))
                    except Exception:
                        return None

                latest = max(
                    (
                        v for v in (
                            get_version(i) for i in range(
                                winreg.QueryInfoKey(hkey)[0]  # type: ignore
                            )
                        )
                        if v is not None
                    )
                )

                with winreg.OpenKeyEx(  # type: ignore
                        hkey, f'{latest}'
                ) as subkey:
                    r_home = winreg.QueryValueEx(  # type: ignore
                        subkey, "InstallPath"
                    )[0]

                # check for an earlier version
                if not r_home:
                    r_home = winreg.QueryValueEx(  # type: ignore
                        hkey, 'InstallPath'
                    )[0]
        except Exception:  # FileNotFoundError, WindowsError, OSError, etc.
            pass
        else:
            # We have a path RHOME
            if sys.version_info[0] == 2:
                # Python 2 path compatibility
                r_home = r_home.encode(sys.getfilesystemencoding())
            # Break the loop, because we have a hit.
            break
    else:
        # for-loop did not break - RHOME is unknown.
        logger.error('Unable to determine R home.')
        r_home = None
    return r_home


def r_ld_library_path_from_subprocess(r_home: str) -> str:
    """Get the LD_LIBRARY_PATH settings added by R."""
    cmd = (os.path.join(r_home, 'bin', 'Rscript'),
           '-e',
           'cat(Sys.getenv("LD_LIBRARY_PATH"))')
    logger.debug('Looking for LD_LIBRARY_PATH with: {}'.format(' '.join(cmd)))
    try:
        r_lib_path = subprocess.check_output(cmd,
                                             universal_newlines=True,
                                             stderr=subprocess.PIPE)
        logger.info(f'R library path: {r_lib_path}')
    except Exception as e:  # FileNotFoundError, WindowsError, etc.
        logger.error(f'Unable to determine R library path: {e}')
        r_lib_path = ''
    logger.info(f'LD_LIBRARY_PATH: {r_lib_path}')
    return r_lib_path


def get_rlib_rpath(r_home: str) -> str:
    """Get the path for the R shared library/libraries."""
    lib_path = os.path.join(r_home, get_r_libnn(r_home))
    return lib_path


# TODO: Does r_ld_library_path_from_subprocess() supersed this?
def get_rlib_path(r_home: str, system: str) -> str:
    """Get the path for the R shared library."""
    if system == 'FreeBSD' or system == 'Linux':
        lib_path = os.path.join(r_home, 'lib', 'libR.so')
    elif system == 'Darwin':
        lib_path = os.path.join(r_home, 'lib', 'libR.dylib')
    elif system == 'Windows':
        # i386
        os.environ['PATH'] = os.pathsep.join(
            (os.environ['PATH'],
             os.path.join(r_home, 'bin', r_version_folder))
        )
        lib_path = os.path.join(r_home, 'bin', r_version_folder, 'R.dll')
    else:
        raise ValueError(
            'The system {system} is currently not supported.'
            .format(system=system)
        )
    return lib_path


def get_r_home() -> Optional[str]:
    """Get R's home directory (aka R_HOME).

    If an environment variable R_HOME is found it is returned,
    and if none is found it is trying to get it from an R executable
    in the PATH. On Windows, a third last attempt is made by trying
    to obtain R_HOME from the registry. If all attempt are unfruitful,
    None is returned.
    """

    r_home = os.environ.get('R_HOME')

    if not r_home:
        try:
            r_home = r_home_from_subprocess()
        except Exception as e:
            if os.name == 'nt':
                r_home = r_home_from_registry()
            if r_home is None:
                logger.error(f'Unable to determine R home: {e}')

    logger.info(f'R home found: {r_home}')
    return r_home


def get_r_exec(r_home: str) -> str:
    """Get the path of the R executable/binary.

    :param: R HOME directory
    :return: Path to the R executable/binary"""

    if sys.platform == 'win32' and '64 bit' in sys.version:
        r_exec = os.path.join(r_home, 'bin', 'x64', 'R')
    else:
        r_exec = os.path.join(r_home, 'bin', 'R')
    logger.info(f'R exec path: {r_exec}')
    return r_exec


def _get_r_cmd_config(r_home: str, about: str, allow_empty=False):
    """Get the output of calling 'R CMD CONFIG <about>'.

    :param r_home: R HOME directory
    :param about: argument passed to the command line 'R CMD CONFIG'
    :param allow_empty: allow the output to be empty
    :return: a tuple (lines of output)"""
    r_exec = get_r_exec(r_home)
    cmd = (r_exec, 'CMD', 'config', about)
    logger.debug('Looking for R CONFIG with: {}'.format(' '.join(cmd)))
    output = subprocess.check_output(
        cmd,
        universal_newlines=True
    ).split(os.linesep)
    # Twist if 'R RHOME' spits out a warning
    if output[0].startswith('WARNING'):
        msg = 'R emitting a warning: {}'.format(output[0])
        warnings.warn(msg)
        logger.debug(msg)
        res = output[1:]
    else:
        res = output
    logger.debug(res)
    return res


def get_r_libnn(r_home: str):
    return _get_r_cmd_config(r_home, 'LIBnn',
                             allow_empty=False)[0]


_R_LIBS = ('LAPACK_LIBS', 'BLAS_LIBS')
_R_FLAGS = ('--ldflags', '--cppflags')


def get_r_flags(r_home: str, flags: str):
    """Get the parsed output of calling 'R CMD CONFIG <about>'.

    Returns a tuple (parsed_args, unknown_args), with parsed_args
    having the attribute `l`, 'L', and 'I'."""

    assert flags in _R_FLAGS

    parser = argparse.ArgumentParser()
    parser.add_argument('-I', action='append')
    parser.add_argument('-L', action='append')
    parser.add_argument('-l', action='append')

    res = shlex.split(
        ' '.join(
            _get_r_cmd_config(r_home, flags,
                              allow_empty=False)))
    return parser.parse_known_args(res)


def get_r_libs(r_home: str, libs: str):
    assert libs in _R_LIBS

    parser = argparse.ArgumentParser()
    parser.add_argument('-I', action='append')
    parser.add_argument('-L', action='append')
    parser.add_argument('-l', action='append')

    res = shlex.split(
        ' '.join(
            _get_r_cmd_config(r_home, libs,
                              allow_empty=False)))
    return parser.parse_known_args(res)


class CExtensionOptions(object):
    """Options to compile C extensions."""

    def __init__(self):
        self.extra_link_args = []
        self.extra_compile_args = ['-std=c99']
        self.include_dirs = []
        self.libraries = []
        self.library_dirs = []

    def add_include(self, args, unknown):
        """Add include directories.

        :param args: args as returned by get_r_flags().
        :param unknown: unknown arguments a returned by get_r_flags()."""
        if args.I is None:
            warnings.warn('No include specified')
        else:
            self.include_dirs.extend(args.I)
        self.extra_compile_args.extend(unknown)

    def add_lib(self, args, unknown, ignore=('R', )):
        """Add libraries.

        :param args: args as returned by get_r_flags().
        :param unknown: unknown arguments a returned by get_r_flags()."""
        if args.L is None:
            if args.l is None:
                # hmmm... no libraries at all
                warnings.warn('No libraries as -l arguments to the compiler.')
            else:
                self.libraries.extend([x for x in args.l if x not in ignore])
        else:
            self.library_dirs.extend(args.L)
            self.libraries.extend(args.l)
        self.extra_link_args.extend(unknown)


def _make_bold_unix(text):
    return '%s%s%s' % ('\033[1m', text, '\033[0m')


def _make_bold_win32(text):
    return text


def iter_info():

    make_bold = _make_bold_win32 if os.name == 'nt' else _make_bold_unix

    yield make_bold('rpy2 version:')
    try:
        # TODO: the repeated import is needed, without which Python
        #   raises an UnboundLocalError (local variable reference before
        #   assignment).
        import rpy2.rinterface  # noqa: F811
        yield rpy2.rinterface_lib.__version__
    except ImportError:
        yield 'rpy2 cannot be imported'

    yield make_bold('Python version:')
    yield sys.version

    yield make_bold("Looking for R's HOME:")

    r_home = os.environ.get('R_HOME')
    yield '    Environment variable R_HOME: %s' % r_home

    r_home_default = None
    if os.name == 'nt':
        r_home_default = r_home_from_registry()
        yield '    InstallPath in the registry: %s' % r_home_default
        r_user = os.environ.get('R_USER')
        yield '    Environment variable R_USER: %s' % r_user
    else:
        try:
            r_home_default = r_home_from_subprocess()
        except Exception as e:
            logger.error(f'Unable to determine R home: {e}')
        yield '    Calling `R RHOME`: %s' % r_home_default

    yield (
        '    Environment variable R_LIBS_USER: %s'
        % os.environ.get('R_LIBS_USER')
    )

    if r_home is not None and r_home_default is not None:
        if os.path.abspath(r_home) != r_home_default:
            yield ('    Warning: The environment variable R_HOME '
                   'differs from the default R in the PATH.')
    else:
        if r_home_default is None:
            yield ('    Warning: There is no R in the PATH and no '
                   'R_HOME defined.')
        else:
            r_home = r_home_default

    # not applicable for Windows
    if os.name != 'nt':
        yield make_bold("R's value for LD_LIBRARY_PATH:")
        if r_home is None:
            yield '     *** undefined when not R home can be determined'
        else:
            yield r_ld_library_path_from_subprocess(r_home)

    try:
        import rpy2.rinterface_lib.openrlib
        rlib_status = 'OK'
    except ImportError as ie:
        try:
            import rpy2
            rlib_status = '*** Error while loading: %s ***' % str(ie)
        except ImportError:
            rlib_status = '*** rpy2 is not installed'
    except OSError as ose:
        rlib_status = str(ose)

    yield make_bold("R version:")
    yield '    In the PATH: %s' % r_version_from_subprocess()
    yield '    Loading R library from rpy2: %s' % rlib_status

    r_libs = os.environ.get('R_LIBS')
    yield make_bold('Additional directories to load R packages from:')
    yield r_libs

    yield make_bold('C extension compilation:')
    c_ext = CExtensionOptions()
    if r_home is None:
        yield ('    Warning: R cannot be found, so no compilation flags '
               'can be extracted.')
    else:
        try:
            c_ext.add_lib(*get_r_flags(r_home, '--ldflags'))
            c_ext.add_include(*get_r_flags(r_home, '--cppflags'))
            yield '  include:'
            yield '  %s' % c_ext.include_dirs
            yield '  libraries:'
            yield '  %s' % c_ext.libraries
            yield '  library_dirs:'
            yield '  %s' % c_ext.library_dirs
            yield '  extra_compile_args:'
            yield '  %s' % c_ext.extra_compile_args
            yield '  extra_link_args:'
            yield '  %s' % c_ext.extra_link_args
        except subprocess.CalledProcessError:
            yield ('    Warning: Unable to get R compilation flags.')

    yield 'Directory for the R shared library:'
    yield get_r_libnn(r_home)

    yield make_bold('CFFI extension type')
    yield f'  Environment variable: {ENVVAR_CFFI_TYPE}'
    yield f'  Value: {get_cffi_mode()}'

    import importlib
    for cffi_type in ('abi', 'api'):
        rinterface_cffi_spec = importlib.util.find_spec(f'_rinterface_cffi_{cffi_type}')
        yield f'  {cffi_type.upper()}: {"PRESENT" if rinterface_cffi_spec else "ABSENT"}'


def set_default_logging():
    logformatter = logging.Formatter('%(name)s: %(message)s')
    loghandler = logging.StreamHandler()
    loghandler.setFormatter(logformatter)
    logger.addHandler(loghandler)
