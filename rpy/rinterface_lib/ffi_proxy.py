import enum


class InterfaceType(enum.Enum):
    ABI = 1
    API = 2


interface_type = InterfaceType.ABI


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


def callback(definition, ffi):
    def decorator(func):
        if interface_type == InterfaceType.ABI:
            res = ffi.callback(definition.callback_def)(func)
        else:
            res = ffi.def_extern(definition.extern_def)(func)
        return res
    return decorator


# Callbacks
_capsule_finalizer_def = SignatureDefinition('_capsule_finalizer',
                                             'void', ('SEXP',))
_evaluate_in_r_def = SignatureDefinition('_evaluate_in_r',
                                         'SEXP', ('SEXP args',))


_consoleflush_def = SignatureDefinition('_consoleflush', 'void', ('void', ))
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
