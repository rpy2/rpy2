import enum
import os
import warnings
from . import _rinterface_capi as _rinterface
from . import callbacks

_options = ('rpy2', '--quiet', '--vanilla', '--no-save')
rpy2_embeddedR_isinitialized = 0x00


# TODO: move initialization-related code to _rinterface ?
class RPY_R_Status(enum.Enum):
    INITIALIZED = 0x01;
    BUSY = 0x02;
    ENDED = 0x04;


def set_initoptions(options):
    if rpy2_embeddedR_isinitialized:
        raise RuntimeError('Options can no longer be set once R is initialized.')
    global _options
    for x in options:
        assert isinstance(x, str)
    _options = tuple(options)


def get_initoptions():
    return _options

    
# TODO: can init_once() be used here ?
def _initr(interactive=True):
    global rpy2_embeddedR_isinitialized
    ffi = _rinterface.ffi
    rlib = _rinterface.rlib
    if rpy2_embeddedR_isinitialized:
        return
    os.environ['R_HOME'] = _rinterface.R_HOME
    options_c = [ffi.new('char[]', o.encode('ASCII')) for o in _options]
    n_options = len(options_c)
    status = rlib.Rf_initialize_R(ffi.cast('int', n_options),
                                  options_c)

    rstart = ffi.new('Rstart')
    rstart.R_Interactive = interactive;

    # TODO: Conditional definition in C code (Aqua, TERM, and TERM not "dumb")
    rlib.R_Outputfile = ffi.NULL;
    rlib.R_Consolefile = ffi.NULL;
    rlib.ptr_R_WriteConsoleEx = callbacks._consolewrite_ex
    rlib.ptr_R_WriteConsole = ffi.NULL
    
    # TODO: Conditional in C code
    _rinterface.rlib.R_SignalHandlers = 0;

    rlib.ptr_R_ShowMessage = callbacks._showmessage
    rlib.ptr_R_ReadConsole = callbacks._consoleread

    rlib.ptr_R_ChooseFile = callbacks._choosefile
    rlib.ptr_R_CleanUp = callbacks._cleanup
    
    rpy2_embeddedR_isinitialized = RPY_R_Status.INITIALIZED

    # TODO: still needed ?
    _rinterface.rlib.R_CStackLimit = ffi.cast('uintptr_t', -1)
    
    _rinterface.rlib.setup_Rmainloop()
    return status


def endr(fatal):
    rlib = _rinterface.rlib
    rlib.R_dot_Last()
    rlib.R_RunExitFinalizers()
    rlib.Rf_KillAllDevices()
    rlib.R_CleanTempDir()
    rlib.R_gc()    
    rlib.Rf_endEmbeddedR(fatal)


class RParsingError(Exception):
    pass


def _parse(cdata, num):
    status = _rinterface.ffi.new('ParseStatus[1]', None)
    res = _rinterface.rlib.Rf_protect(
        _rinterface.rlib.R_ParseVector(
            cdata, # text
            num,
            status,
            _rinterface.rlib.R_NilValue)
    )
    # TODO: design better handling of possible status:
    # PARSE_NULL,
    # PARSE_OK,
    # PARSE_INCOMPLETE,
    # PARSE_ERROR,
    # PARSE_EOF
    if status[0] != _rinterface.rlib.PARSE_OK:
        _rinterface.rlib.Rf_unprotect(1)
        raise RParsingError(status)
    _rinterface.rlib.Rf_unprotect(1)
    return res 
