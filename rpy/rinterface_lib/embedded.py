import enum
import os
import sys
import typing
import warnings
from _rinterface_cffi import ffi
from . import openrlib
from . import callbacks

_options = ('rpy2', '--quiet', '--no-save')
rpy2_embeddedR_isinitialized = 0x00


# TODO: move initialization-related code to _rinterface ?
class RPY_R_Status(enum.Enum):
    INITIALIZED = 0x01
    BUSY = 0x02
    ENDED = 0x04


def set_initoptions(options: typing.Tuple[str]) -> None:
    if rpy2_embeddedR_isinitialized:
        raise RuntimeError('Options can no longer be set once '
                           'R is initialized.')
    global _options
    for x in options:
        assert isinstance(x, str)
    _options = tuple(options)


def get_initoptions() -> typing.Tuple[str]:
    return _options


def isinitialized() -> bool:
    """Is the embedded R initialized."""
    return bool(rpy2_embeddedR_isinitialized & RPY_R_Status.INITIALIZED.value)


def setinitialized() -> None:
    global rpy2_embeddedR_isinitialized
    rpy2_embeddedR_isinitialized = RPY_R_Status.INITIALIZED.value


def isready() -> bool:
    """Is the embedded R ready for use."""
    INITIALIZED = RPY_R_Status.INITIALIZED
    return bool(
        rpy2_embeddedR_isinitialized == INITIALIZED.value
    )


def assert_isready():
    if not isready():
        raise RNotReadyError(
            'The embedded R is not ready to use.')


class RNotReadyError(Exception):
    """Embedded R is not ready to use."""
    pass


class RRuntimeError(Exception):
    pass


# TODO: can init_once() be used here ?
def _initr(interactive: bool = True) -> int:
    rlib = openrlib.rlib
    if isinitialized():
        return
    os.environ['R_HOME'] = openrlib.R_HOME
    options_c = [ffi.new('char[]', o.encode('ASCII')) for o in _options]
    n_options = len(options_c)
    status = rlib.Rf_initialize_R(ffi.cast('int', n_options),
                                  options_c)

    rstart = ffi.new('Rstart')
    rstart.R_Interactive = interactive

    # TODO: Conditional definition in C code (Aqua, TERM, and TERM not "dumb")
    rlib.R_Outputfile = ffi.NULL
    rlib.R_Consolefile = ffi.NULL
    rlib.ptr_R_WriteConsoleEx = callbacks._consolewrite_ex
    rlib.ptr_R_WriteConsole = ffi.NULL

    # TODO: Conditional in C code
    rlib.R_SignalHandlers = 0

    rlib.ptr_R_ShowMessage = callbacks._showmessage
    rlib.ptr_R_ReadConsole = callbacks._consoleread
    rlib.ptr_R_FlushConsole = callbacks._consoleflush
    rlib.ptr_R_ResetConsole = callbacks._consolereset

    rlib.ptr_R_ChooseFile = callbacks._choosefile
    rlib.ptr_R_ShowFiles = callbacks._showfiles

    rlib.ptr_R_CleanUp = callbacks._cleanup

    setinitialized()

    # TODO: still needed ?
    rlib.R_CStackLimit = ffi.cast('uintptr_t', -1)

    rlib.setup_Rmainloop()
    return status


def endr(fatal: int) -> None:
    global rpy2_embeddedR_isinitialized
    rlib = openrlib.rlib
    if rpy2_embeddedR_isinitialized & RPY_R_Status.ENDED.value:
        return
    rlib.R_dot_Last()
    rlib.R_RunExitFinalizers()
    rlib.Rf_KillAllDevices()
    rlib.R_CleanTempDir()
    rlib.R_gc()
    rlib.Rf_endEmbeddedR(fatal)
    rpy2_embeddedR_isinitialized ^= RPY_R_Status.ENDED.value


_REFERENCE_TO_R_SESSIONS = 'https://github.com/rstudio/reticulate/issues/98'
_R_SESSION_INITIALIZED = 'R_SESSION_INITIALIZED'
_PYTHON_SESSION_INITIALIZED = 'PYTHON_SESSION_INITIALIZED'


def get_r_session_status(r_session_init=None) -> dict:
    """Return information about the R session, if available.

    Information about the R session being already initialized can be
    communicated by an environment variable exported by the process that
    initialized it. See discussion at:
    %s
    """ % _REFERENCE_TO_R_SESSIONS

    res = {'current_pid': os.getpid()}

    if r_session_init is None:
        r_session_init = os.environ.get(_R_SESSION_INITIALIZED)
    if r_session_init:
        for item in r_session_init.split(':'):
            try:
                key, value = item.split('=', 1)
            except ValueError:
                warnings.warn(
                    'The item %s in %s should be of the form key=value.' %
                    (item, _R_SESSION_INITIALIZED)
                )
            res[key] = value
    return res


def is_r_externally_initialized() -> bool:
    r_status = get_r_session_status()
    return str(r_status['current_pid']) == str(r_status.get('PID'))


def set_python_process_info() -> None:
    """Set information about the Python process in an environment variable.

    Current the information See discussion at:
    %s
    """ % _REFERENCE_TO_R_SESSIONS

    info = (('current_pid', os.getpid()),
            ('sys.executable', sys.executable))
    info_string = ':'.join('%s=%s' % x for x in info)
    os.environ[_PYTHON_SESSION_INITIALIZED] = info_string


# R environments, initialized with rpy2.rinterface.SexpEnvironment
# objects when R is initialized.
emptyenv = None
baseenv = None
globalenv = None
