import collections
import enum
import logging
import os
import sys
import typing
import warnings
from rpy2.rinterface_lib import openrlib
from rpy2.rinterface_lib import callbacks
from typing import Protocol

logger = logging.getLogger(__name__)

ffi = openrlib.ffi

# Container for module-level C objects needing to be protected from garbage
# collection on the Python side.
__cffi_protected = {}

_options = ('rpy2', '--quiet', '--no-save')  # type: typing.Tuple[str, ...]
logger.info('Default options to initialize R: {}'.format(', '.join(_options)))

# These constants are default values from R sources
_DEFAULT_VSIZE: int = 67108864  # vector heap size
_DEFAULT_NSIZE: int = 350000  # language heap size
_DEFAULT_MAX_VSIZE: int = sys.maxsize  # max vector heap size
_DEFAULT_MAX_NSIZE: int = 50000000  # max language heap size
_DEFAULT_PPSIZE: int = 50000  # stack size
_DEFAULT_C_STACK_LIMIT: int = -1
_DEFAULT_R_INTERACTIVE: bool = True

rpy2_embeddedR_isinitialized = 0x00


class Is_RStart(Protocol):
    @property
    def rhome(self): ...

    @rhome.setter
    def rhome(self, value) -> None: ...

    @property
    def home(self): ...

    @home.setter
    def home(self, value) -> None: ...

    @property
    def CharacterMode(self): ...

    @CharacterMode.setter
    def CharacterMode(self, value) -> None: ...

    @property
    def ReadConsole(self): ...

    @ReadConsole.setter
    def ReadConsole(self, value) -> None: ...

    @property
    def WriteConsoleEx(self): ...

    @WriteConsoleEx.setter
    def WriteConsoleEx(self, value) -> None: ...

    @property
    def CallBack(self): ...

    @CallBack.setter
    def CallBack(self, value) -> None: ...

    @property
    def ShowMessage(self): ...

    @ShowMessage.setter
    def ShowMessage(self, value) -> None: ...

    @property
    def YesNoCancel(self): ...

    @YesNoCancel.setter
    def YesNoCancel(self, value) -> None: ...

    @property
    def Busy(self): ...

    @Busy.setter
    def Busy(self, value) -> None: ...

    @property
    def R_Quiet(self): ...

    @R_Quiet.setter
    def R_Quiet(self, value) -> None: ...

    @property
    def R_Interactive(self): ...

    @R_Interactive.setter
    def R_Interactive(self, value) -> None: ...

    @property
    def RestoreAction(self): ...

    @RestoreAction.setter
    def RestoreAction(self, value) -> None: ...

    @property
    def SaveAction(self): ...

    @SaveAction.setter
    def SaveAction(self, value) -> None: ...

    @property
    def vsize(self): ...

    @vsize.setter
    def vsize(self, value) -> None: ...

    @property
    def nsize(self): ...

    @nsize.setter
    def nsize(self, value) -> None: ...

    @property
    def max_vsize(self): ...

    @max_vsize.setter
    def max_vsize(self, value) -> None: ...

    @property
    def max_nsize(self): ...

    @max_nsize.setter
    def max_nsize(self, value) -> None: ...

    @property
    def ppsize(self): ...

    @ppsize.setter
    def ppsize(self, value) -> None: ...


rstart: Is_RStart = None  # type: ignore


def _build_rstart(rhome, interactive, setcallbacks):
    rstart = ffi.new('Rstart')
    __cffi_protected['rstart'] = rstart
    openrlib.rlib.R_DefParams(rstart)
    rstart.rhome = rhome
    userhome = ffi.new("char[]", ffi.string(openrlib.rlib.getRUser()))
    __cffi_protected['userhome'] = userhome
    rstart.home = userhome
    rstart.CharacterMode = openrlib.rlib.LinkDLL
    if setcallbacks:
        for cb in CALLBACK_INIT_PAIRS:
            if cb.c_name_nt and cb.py_name:
                setattr(rstart, cb.c_name_nt,
                        getattr(callbacks, cb.py_name))

    rstart.R_Quiet = True
    rstart.R_Interactive = interactive
    rstart.RestoreAction = openrlib.rlib.SA_RESTORE
    rstart.SaveAction = openrlib.rlib.SA_NOSAVE

    rstart.vsize = ffi.cast('size_t', _DEFAULT_VSIZE)
    rstart.nsize = ffi.cast('size_t', _DEFAULT_NSIZE)
    rstart.max_vsize = ffi.cast('size_t', _DEFAULT_MAX_VSIZE)
    rstart.max_nsize = ffi.cast('size_t', _DEFAULT_MAX_NSIZE)
    rstart.ppsize = ffi.cast('size_t', _DEFAULT_PPSIZE)
    return rstart


# TODO: move initialization-related code to _rinterface ?
class RPY_R_Status(enum.Enum):
    """Possible status for the embedded R."""
    INITIALIZED = 0x01
    BUSY = 0x02
    ENDED = 0x04


def set_initoptions(options: typing.Tuple[str]) -> None:
    """Set initialization options for the embedded R.

    :param:`options` A tuple of string with the options
    (e.g., '--verbose', '--quiet').
    """
    if rpy2_embeddedR_isinitialized:
        raise RuntimeError('Options can no longer be set once '
                           'R is initialized.')
    global _options
    for x in options:
        assert isinstance(x, str)
    with openrlib.rlock:
        logger.info('Setting options to initialize R: {}'
                    .format(', '.join(options)))
        _options = tuple(options)


def get_initoptions() -> typing.Tuple[str, ...]:
    """Get the initialization options for the embedded R."""
    return _options


def isinitialized() -> bool:
    """Is the embedded R initialized."""
    return bool(rpy2_embeddedR_isinitialized & RPY_R_Status.INITIALIZED.value)


def _setinitialized() -> None:
    """Set the embedded R as initialized.

    This may result in a later segfault if used with the embedded R has not
    been initialized. You should not have to use it."""
    global rpy2_embeddedR_isinitialized
    rpy2_embeddedR_isinitialized = RPY_R_Status.INITIALIZED.value


def isready() -> bool:
    """Is the embedded R ready for use."""
    INITIALIZED = RPY_R_Status.INITIALIZED
    return bool(
        rpy2_embeddedR_isinitialized == INITIALIZED.value
    )


def assert_isready() -> None:
    """Assert whether R is ready (initialized).

    Raises an RNotReadyError if it is not."""
    if not isready():
        raise RNotReadyError(
            'The embedded R is not ready to use.')


class RNotReadyError(Exception):
    """Embedded R is not ready to use."""
    pass


class RRuntimeError(Exception):
    """Error generated by R."""
    pass


def _setcallback(rlib, rlib_symbol: str,
                 callbacks,
                 callback_symbol: typing.Optional[str]) -> None:
    """Set R callbacks.

    :param rlib: Namespace
    :param rlib_symbol: Symbol (name) in the namespace in which to place
      the new callback function
    :param callbacks: Namespace in which to find the callback function.
    :param callbacks_symbol: Symbol (name) of the new callback function.
"""
    if callback_symbol is None:
        new_callback = ffi.NULL
    else:
        new_callback = getattr(callbacks, callback_symbol)
    setattr(rlib, rlib_symbol, new_callback)


_CallbackInit = collections.namedtuple(
    '_CallbackInit',
    ('c_name_posix', 'c_name_nt', 'py_name')
)

CALLBACK_INIT_PAIRS: typing.Tuple[_CallbackInit, ...] = (
    _CallbackInit('ptr_R_WriteConsoleEx', 'WriteConsoleEx', '_consolewrite_ex'),
    _CallbackInit('ptr_R_WriteConsole', 'WriteConsole', None),
    _CallbackInit('ptr_R_ShowMessage', 'ShowMessage', '_showmessage'),
    _CallbackInit('ptr_R_ReadConsole', 'ReadConsole', '_consoleread'),
    _CallbackInit('ptr_R_FlushConsole', None, '_consoleflush'),
    _CallbackInit('ptr_R_ResetConsole', None, '_consolereset'),
    _CallbackInit('ptr_R_ChooseFile', None, '_choosefile'),
    _CallbackInit('ptr_R_ShowFiles', None, '_showfiles'),
    _CallbackInit('ptr_R_CleanUp', None, '_cleanup'),
    _CallbackInit('ptr_R_ProcessEvents', None, '_processevents'),
    _CallbackInit(None, 'YesNoCancel', '_yesnocancel'),
    _CallbackInit(None, 'CallBack', '_callback'),
    _CallbackInit('ptr_R_Busy', 'Busy', '_busy'),
)


def _initr(
        interactive: typing.Optional[bool] = None,
        _want_setcallbacks: bool = True,
        _c_stack_limit: typing.Optional[int] = None
) -> typing.Optional[int]:
    """Initialize the embedded R.

    :param interactive: Should R run in interactive or non-interactive mode?
    if `None` the value in `_DEFAULT_R_INTERACTIVE` will be used.
    :param _want_setcallbacks: Should custom rpy2 callbacks for R frontends
    be set?.
    :param _c_stack_limit: Limit for the C Stack.
    if `None` the value in `_DEFAULT_C_STACK_LIMIT` will be used.
    """

    if interactive is None:
        interactive = _DEFAULT_R_INTERACTIVE
    if _c_stack_limit is None:
        _c_stack_limit = _DEFAULT_C_STACK_LIMIT

    rlib = openrlib.rlib
    ffi_proxy = openrlib.ffi_proxy
    if (
            ffi_proxy.get_ffi_mode(openrlib._rinterface_cffi)
            ==
            ffi_proxy.InterfaceType.ABI
    ):
        callback_funcs = callbacks
    else:
        callback_funcs = rlib

    with openrlib.rlock:
        if isinitialized():
            logger.info('R is already initialized. No need to initialize.')
            return None
        elif openrlib.rlib.R_NilValue != ffi.NULL:
            msg = ('R was initialized outside of rpy2 (R_NilValue != NULL). '
                   'Trying to use it nevertheless.')
            warnings.warn(msg)
            logger.warn(msg)
            _setinitialized()
            return None

        # TODO: Setting LD_LIBRARY_PATH after the process has started
        # is too late. Because of this, the line below does not help
        # address issues where calling R from the command line is working
        # (as it is a shell script setting environment variables before
        # start the binary in a child process). Calling C's dlopen with
        # the path of the shared library could address this but for the
        # API mode this would require writing a C wrapper to manually
        # load each each symbol in the C library.
        options_c = [ffi.new('char[]', o.encode('ASCII')) for o in _options]
        n_options = len(options_c)
        n_options_c = ffi.cast('int', n_options)

        if os.name == 'nt':
            status = openrlib.rlib.Rf_initEmbeddedR(n_options_c, options_c)
            _setinitialized()

            rhome = openrlib.rlib.get_R_HOME()
            __cffi_protected['rhome'] = rhome
            rstart = _build_rstart(rhome, interactive, _want_setcallbacks)
            openrlib.rlib.R_SetParams(rstart)

            # TODO: still needed ?
            openrlib.rlib.R_CStackLimit = ffi.cast('uintptr_t', _c_stack_limit)
        else:
            if openrlib.R_HOME is None:
                raise ValueError('openrlib.R_HOME cannot be None.')
            else:
                os.environ['R_HOME'] = openrlib.R_HOME

            # TODO: Conditional in C code
            rlib.R_SignalHandlers = 0

            # Instead of calling Rf_initEmbeddedR which breaks threaded context
            # perform the initialization manually to set R_CStackLimit before
            # calling setup_Rmainloop(), see:
            # https://github.com/rpy2/rpy2/issues/729
            rlib.Rf_initialize_R(n_options_c, options_c)
            if _c_stack_limit:
                rlib.R_CStackLimit = ffi.cast('uintptr_t', _c_stack_limit)
            rlib.R_Interactive = True
            logger.debug('Calling R setup_Rmainloop.')
            rlib.setup_Rmainloop()

            _setinitialized()

            rlib.R_Interactive = interactive

            # TODO: Conditional definition in C code
            #   (Aqua, TERM, and TERM not "dumb")
            rlib.R_Outputfile = ffi.NULL
            rlib.R_Consolefile = ffi.NULL

            if _want_setcallbacks:
                logger.debug('Setting functions for R callbacks.')
                for cb in CALLBACK_INIT_PAIRS:
                    if cb.c_name_posix:
                        _setcallback(rlib, cb.c_name_posix,
                                     callback_funcs, cb.py_name)
            status = 1
    return status


def endr(fatal: int) -> None:
    logger.debug('Ending embedded R process.')
    global rpy2_embeddedR_isinitialized
    rlib = openrlib.rlib
    with openrlib.rlock:
        if rpy2_embeddedR_isinitialized & RPY_R_Status.ENDED.value:
            logger.info('Embedded R already ended.')
            return
        logger.debug('R_do_Last()')
        rlib.R_dot_Last()
        logger.debug('R_RunExitFinalizers()')
        rlib.R_RunExitFinalizers()
        logger.debug('Rf_KillAllDevices()')
        rlib.Rf_KillAllDevices()
        logger.debug('R_CleanTempDir()')
        rlib.R_CleanTempDir()
        logger.debug('R_gc')
        rlib.R_gc()
        logger.debug('Rf_endEmbeddedR(fatal)')
        rlib.Rf_endEmbeddedR(fatal)
        rpy2_embeddedR_isinitialized ^= RPY_R_Status.ENDED.value
        logger.info('Embedded R ended.')


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

    See discussion at:
    %s
    """ % _REFERENCE_TO_R_SESSIONS

    info = (('current_pid', os.getpid()),
            ('sys.executable', sys.executable))
    info_string = ':'.join('%s=%s' % x for x in info)
    os.environ[_PYTHON_SESSION_INITIALIZED] = info_string
