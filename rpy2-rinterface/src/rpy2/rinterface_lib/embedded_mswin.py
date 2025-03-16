import sys
import typing
import rpy2.situation
from rpy2.rinterface_lib import embedded
from rpy2.rinterface_lib import callbacks
from rpy2.rinterface_lib import openrlib

ffi = openrlib.ffi

# These constants are default values from R sources
_DEFAULT_VSIZE: int = 67108864  # vector heap size
_DEFAULT_NSIZE: int = 350000  # language heap size
_DEFAULT_MAX_VSIZE: int = sys.maxsize  # max vector heap size
_DEFAULT_MAX_NSIZE: int = 50000000  # max language heap size
_DEFAULT_PPSIZE: int = 50000  # stack size
_DEFAULT_C_STACK_LIMIT: int = -1
_DEFAULT_R_INTERACTIVE: bool = True

CALLBACK_INIT_PAIRS = (('WriteConsoleEx', '_consolewrite_ex'),
                       ('WriteConsole', None),
                       ('ShowMessage', '_showmessage'),
                       ('ReadConsole', '_consoleread'),
                       ('Busy', '_busy'))

__cffi_protected = {}


def _build_rstart(rhome, interactive, setcallbacks):
    rstart = ffi.new('Rstart')
    embedded.rstart = rstart
    __cffi_protected['rstart'] = rstart
    openrlib.rlib.R_DefParams(rstart)
    # TODO: A cleanup / consolidation of "R HOME"
    # definition is needed.
    print(f'rhome: {rhome}')
    rstart.rhome = rhome
    userhome = ffi.new("char[]", ffi.string(openrlib.rlib.getRUser()))
    __cffi_protected['userhome'] = userhome
    rstart.home = userhome
    rstart.R_Quiet = True
    rstart.R_Slave = False
    rstart.R_Interactive = interactive
    # TODO: Force verbose for now.
    rstart.R_Verbose = True
    rstart.LoadSiteFile = True
    rstart.LoadInitFile = True
    rstart.RestoreAction = openrlib.rlib.SA_RESTORE
    rstart.SaveAction = openrlib.rlib.SA_NOSAVE
    rstart.CharacterMode = openrlib.rlib.LinkDLL  # 1?
    if False and setcallbacks:
        if openrlib.cffi_mode is rpy2.situation.CFFI_MODE.ABI:
            callback_funcs = callbacks
        else:
            callback_funcs = openrlib.rlib

        for rstart_symbol, callback_symbol in CALLBACK_INIT_PAIRS:
            embedded._setcallback(rstart, rstart_symbol,
                                  callback_funcs, callback_symbol)

    rstart.vsize = ffi.cast('size_t', _DEFAULT_VSIZE)
    rstart.nsize = ffi.cast('size_t', _DEFAULT_NSIZE)
    rstart.max_vsize = ffi.cast('size_t', _DEFAULT_MAX_VSIZE)
    rstart.max_nsize = ffi.cast('size_t', _DEFAULT_MAX_NSIZE)
    rstart.ppsize = ffi.cast('size_t', _DEFAULT_PPSIZE)
    return rstart


def _initr_win32(
        interactive: typing.Optional[bool] = None,
        _want_setcallbacks: bool = False,
        _c_stack_limit: typing.Optional[int] = _DEFAULT_C_STACK_LIMIT

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

    with openrlib.rlock:
        if embedded.isinitialized():
            return None

        options_c = [ffi.new('char[]', o.encode('ASCII'))
                     for o in embedded._options]
        n_options = len(options_c)
        n_options_c = ffi.cast('int', n_options)
        status = openrlib.rlib.Rf_initialize_R(n_options_c, options_c)
        embedded._setinitialized()

        rhome = openrlib.rlib.get_R_HOME()
        __cffi_protected['rhome'] = rhome
        embedded.rstart = _build_rstart(rhome, interactive, _want_setcallbacks)
        openrlib.rlib.R_SetParams(embedded.rstart)

        # TODO: still needed ?
        openrlib.rlib.R_CStackLimit = ffi.cast('uintptr_t', _c_stack_limit)
        openrlib.rlib.setup_Rmainloop()
        

        return status
