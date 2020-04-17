from . import embedded
from . import callbacks
from . import openrlib

ffi = openrlib.ffi

_DEFAULT_C_STACK_LIMIT = -1


def _initr_win32(
        interactive: bool = True,
        _want_setcallbacks: bool = True,
        _c_stack_limit: int = _DEFAULT_C_STACK_LIMIT

) -> int:
    with openrlib.rlock:
        if embedded.isinitialized():
            return None

        embedded.rstart = ffi.new('Rstart')
        rstart = embedded.rstart
        rstart.rhome = openrlib.rlib.get_R_HOME()
        rstart.home = openrlib.rlib.getRUser()
        rstart.CharacterMode = openrlib.rlib.LinkDLL
        if _want_setcallbacks:
            rstart.ReadConsole = callbacks._consoleread
            rstart.WriteConsoleEx = callbacks._consolewrite_ex
            rstart.CallBack = callbacks._callback
            rstart.ShowMessage = callbacks._showmessage
            rstart.YesNoCancel = callbacks._yesnocancel
            rstart.Busy = callbacks._busy
    
        rstart.R_Quiet = True
        rstart.R_Interactive = interactive
        rstart.RestoreAction = openrlib.rlib.SA_RESTORE
        rstart.SaveAction = openrlib.rlib.SA_NOSAVE
    
        options_c = [ffi.new('char[]', o.encode('ASCII'))
                     for o in embedded._options]
        n_options = len(options_c)
        n_options_c = ffi.cast('int', n_options)
        status = openrlib.rlib.Rf_initEmbeddedR(n_options_c, options_c)
        embedded.setinitialized()
    
        # TODO: still needed ?
        openrlib.rlib.R_CStackLimit = ffi.cast('uintptr_t', _c_stack_limit)
    
        openrlib.rlib.R_SetParams(rstart)
    
        return status
