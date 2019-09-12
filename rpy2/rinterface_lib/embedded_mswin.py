from . import embedded
from . import callbacks
from . import openrlib

ffi = openrlib.ffi


def _initr_win32(interactive: bool = True) -> int:
    embedded.rstart = ffi.new('Rstart')
    rstart = embedded.rstart
    rstart.rhome = openrlib.rlib.get_R_HOME()
    rstart.home = openrlib.rlib.getRUser()
    rstart.CharacterMode = openrlib.rlib.LinkDLL
    rstart.ReadConsole = callbacks._consoleread
    rstart.WriteConsole = callbacks._consolewrite_ex
    rstart.CallBack = callbacks._callback
    rstart.ShowMessage = callbacks._showmessage
    rstart.YesNoCancel = callbacks._yesnocancel
    rstart.Busy = callbacks._busy

    rstart.R_Quiet = True
    rstart.R_Interactive = interactive
    rstart.RestoreAction = openrlib.rlib.SA_RESTORE
    rstart.SaveAction = openrlib.rlib.SA_NOSAVE

    embedded.setinitialized()

    # TODO: still needed ?
    openrlib.rlib.R_CStackLimit = ffi.cast('uintptr_t', -1)

    openrlib.rlib.setup_Rmainloop()
    return 1
