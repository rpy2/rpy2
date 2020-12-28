import enum
import os


class InterfaceType(enum.Enum):
    ABI = 1
    API = 2


class SignatureDefinition(object):

    def __init__(self, name, rtype, arguments):
        self.name = name
        self.rtype = rtype
        self.arguments = arguments

    @property
    def callback_def(self):
        return '{} ({})'.format(self.rtype, ' ,'.join(self.arguments))

    @property
    def extern_def(self):
        return '{} {}({})'.format(
            self.rtype, self.name, ' ,'.join(self.arguments)
        )

    @property
    def extern_python_def(self):
        return 'extern "Python" {} {}({});'.format(
            self.rtype, self.name, ' ,'.join(self.arguments)
        )


def get_ffi_mode(_rinterface_cffi):
    if hasattr(_rinterface_cffi, 'lib'):
        return InterfaceType.API
    else:
        return InterfaceType.ABI


def callback(definition, _rinterface_cffi):
    def decorator(func):
        if get_ffi_mode(_rinterface_cffi) == InterfaceType.ABI:
            res = _rinterface_cffi.ffi.callback(definition.callback_def)(func)
        elif get_ffi_mode(_rinterface_cffi) == InterfaceType.API:
            res = _rinterface_cffi.ffi.def_extern()(func)
        else:
            raise RuntimeError('The cffi mode is neither ABI or API.')
        return res
    return decorator


# Callbacks
_capsule_finalizer_def = SignatureDefinition('_capsule_finalizer',
                                             'void', ('SEXP',))
_evaluate_in_r_def = SignatureDefinition('_evaluate_in_r',
                                         'SEXP', ('SEXP args',))


_consoleflush_def = SignatureDefinition('_consoleflush', 'void', ('void', ))
if os.name == 'nt':
    _consoleread_def = SignatureDefinition('_consoleread', 'int',
                                           ('char *', 'char *',
                                            'int', 'int'))
else:
    _consoleread_def = SignatureDefinition('_consoleread', 'int',
                                           ('char *', 'unsigned char *',
                                            'int', 'int'))
_consolereset_def = SignatureDefinition('_consolereset', 'void', ('void', ))
_consolewrite_def = SignatureDefinition('_consolewrite', 'void',
                                        ('char *', 'int'))
_consolewrite_ex_def = SignatureDefinition('_consolewrite_ex', 'void',
                                           ('char *', 'int', 'int'))
_showmessage_def = SignatureDefinition('_showmessage', 'void', ('char *', ))
_choosefile_def = SignatureDefinition('_choosefile', 'int',
                                      ('int', 'char *', 'int'))
_cleanup_def = SignatureDefinition('_cleanup', 'void',
                                   ('SA_TYPE', 'int', 'int'))
_showfiles_def = SignatureDefinition('_showfiles', 'int',
                                     ('int', 'const char **', 'const char **',
                                      'const char *', 'Rboolean',
                                      'const char *'))
_processevents_def = SignatureDefinition('_processevents', 'void', ('void', ))
_busy_def = SignatureDefinition('_busy', 'void', ('int', ))
_callback_def = SignatureDefinition('_callback', 'void', ('void', ))
# TODO: should be const char *
_yesnocancel_def = SignatureDefinition('_yesnocancel', 'int', ('char *', ))

_parsevector_wrap_def = SignatureDefinition('_parsevector_wrap',
                                            'SEXP', ('void *data', ))

_handler_def = SignatureDefinition('_handler_wrap',
                                   'SEXP', ('SEXP cond', 'void *hdata'))

_exec_findvar_in_frame_def = SignatureDefinition('_exec_findvar_in_frame',
                                                 'void', ('void *data', ))
