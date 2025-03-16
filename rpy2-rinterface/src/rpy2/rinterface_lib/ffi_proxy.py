import enum
import logging
import os
import sys
import types
import typing

logger: logging.Logger = logging.getLogger(__name__)


class InterfaceType(enum.Enum):
    ABI = 1
    API = 2


class SignatureDefinition(object):

    def __init__(self, name: str, rtype: str,
                 arguments: typing.Tuple[str, ...]):
        self.name = name
        self.rtype = rtype
        self.arguments = arguments

    @property
    def callback_def(self) -> str:
        return '{} ({})'.format(self.rtype, ', '.join(self.arguments))

    @property
    def extern_def(self) -> str:
        return '{} {}({})'.format(
            self.rtype, self.name, ', '.join(self.arguments)
        )

    @property
    def extern_python_def(self) -> str:
        return 'extern "Python" {} {}({});'.format(
            self.rtype, self.name, ', '.join(self.arguments)
        )


FFI_MODE: typing.Optional[InterfaceType] = None


def get_ffi_mode(_rinterface_cffi: types.ModuleType) -> InterfaceType:
    global FFI_MODE
    if FFI_MODE is None:
        if hasattr(_rinterface_cffi, 'lib'):
            res = InterfaceType.API
        else:
            res = InterfaceType.ABI
        logger.debug(f'cffi mode is {res}')
        FFI_MODE = res
    return FFI_MODE


def _callback_wrapper_ABI(func, onerror):
    """
    :param:func: a callback function.
    :param:onerror: a callback to run if there is an error.
    :returns: a closure wrapping `func`.
    """
    def outer_func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            onerror(exc_type, exc_value, exc_traceback)
    return outer_func


def callback(
        definition, _rinterface_cffi,
        error=None, onerror=None
) -> typing.Callable[[typing.Callable], object]:
    def decorator(func: typing.Callable) -> object:
        if get_ffi_mode(_rinterface_cffi) == InterfaceType.ABI:
            res = _rinterface_cffi.ffi.callback(definition.callback_def)(
                _callback_wrapper_ABI(func, onerror)
            )
        elif get_ffi_mode(_rinterface_cffi) == InterfaceType.API:
            res = _rinterface_cffi.ffi.def_extern(
                error=error, onerror=onerror
            )(func)
        else:
            raise RuntimeError('The cffi mode is neither ABI or API.')
        return res
    return decorator


# Callbacks
_capsule_finalizer_def: SignatureDefinition = SignatureDefinition(
    '_capsule_finalizer',
    'void', ('SEXP',))

_evaluate_in_r_def: SignatureDefinition = SignatureDefinition(
    '_evaluate_in_r',
    'SEXP', ('SEXP args',))

_consoleflush_def: SignatureDefinition = SignatureDefinition(
    '_consoleflush', 'void', ('void', ))

_consoleread_def: SignatureDefinition = SignatureDefinition(
    '_consoleread', 'int',
    ('char *',
     'char *' if os.name == 'nt' else 'unsigned char *',
     'int', 'int'))

_consolereset_def: SignatureDefinition = SignatureDefinition(
    '_consolereset', 'void', ('void', ))
_consolewrite_def: SignatureDefinition = SignatureDefinition(
    '_consolewrite', 'void',
    ('char *', 'int'))
_consolewrite_ex_def: SignatureDefinition = SignatureDefinition(
    '_consolewrite_ex', 'void',
    ('char *', 'int', 'int'))
_showmessage_def: SignatureDefinition = SignatureDefinition(
    '_showmessage', 'void', ('char *', ))
_choosefile_def: SignatureDefinition = SignatureDefinition(
    '_choosefile', 'int',
    ('int', 'char *', 'int'))
_cleanup_def: SignatureDefinition = SignatureDefinition(
    '_cleanup', 'void',
    ('SA_TYPE', 'int', 'int'))
_showfiles_def: SignatureDefinition = SignatureDefinition(
    '_showfiles', 'int',
    ('int', 'const char **', 'const char **',
     'const char *', 'Rboolean',
     'const char *'))
_processevents_def: SignatureDefinition = SignatureDefinition(
    '_processevents', 'void', ('void', ))
_busy_def: SignatureDefinition = SignatureDefinition(
    '_busy', 'void', ('int', ))
_callback_def: SignatureDefinition = SignatureDefinition(
    '_callback', 'void', ('void', ))
# TODO: should be const char *
_yesnocancel_def: SignatureDefinition = SignatureDefinition(
    '_yesnocancel', 'int', ('char *', ))

_parsevector_wrap_def: SignatureDefinition = SignatureDefinition(
    '_parsevector_wrap',
    'SEXP', ('void *data', ))

_handler_def: SignatureDefinition = SignatureDefinition(
    '_handler_wrap',
    'SEXP', ('SEXP cond', 'void *hdata'))

_exec_findvar_in_frame_def: SignatureDefinition = SignatureDefinition(
    '_exec_findvar_in_frame',
    'void', ('void *data', ))
