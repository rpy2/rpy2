import enum
import os
import typing
from _rinterface_cffi import ffi
from . import openrlib
from . import callbacks

_options = ('rpy2', '--quiet', '--vanilla', '--no-save')
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


def isready() -> bool:
    """Is the embedded R ready for use."""
    INITIALIZED = RPY_R_Status.INITIALIZED
    return bool(
        rpy2_embeddedR_isinitialized == INITIALIZED.value
    )


class RNotReadyError(Exception):
    """Embedded R is not ready to use."""
    pass


class RRuntimeError(Exception):
    pass


# TODO: can init_once() be used here ?
def _initr(interactive: bool = True) -> int:
    global rpy2_embeddedR_isinitialized

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

    rlib.ptr_R_ChooseFile = callbacks._choosefile

    rlib.ptr_R_ShowFiles = callbacks._showfiles

    rlib.ptr_R_CleanUp = callbacks._cleanup

    rpy2_embeddedR_isinitialized = RPY_R_Status.INITIALIZED.value

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


# R environments, initialized with rpy2.rinterface.SexpEnvironment
# objects when R is initialized.
emptyenv = None
baseenv = None
globalenv = None
