import cffi
import os
import re
import rpy2.situation
from rpy2.rinterface_lib import ffi_proxy

ffibuilder_abi = cffi.FFI()
ffibuilder_api = cffi.FFI()

ifdef_pat = re.compile('^#ifdef +([^ ]+) *$')
define_pat = re.compile('^#define +([^ ]+) +([^ ]+) *$')

cdef = []
definitions = {}


if ffibuilder_abi.sizeof('size_t') > 4:
    LONG_VECTOR_SUPPORT = True
    R_XLEN_T_MAX = 4503599627370496
    R_SHORT_LEN_MAX = 2147483647
    definitions['RPY2_RLEN_LONG'] = True
else:
    definitions['RPY2_RLEN_SHORT'] = True


if os.name == 'nt':
    definitions['OSNAME_NT'] = True


def parse(iterrows, rownum, until=None):
    res = []
    for row_i, row in enumerate(iter(iterrows), rownum):
        if until and row.startswith(until):
            break
        m = ifdef_pat.match(row)
        if m:
            defined = m.groups()[0].strip()
            block = parse(iterrows, row_i, until='#endif')
            if defined in definitions:
                res.extend(block)
            continue
        m = define_pat.match(row)
        if m:
            alias, value = m.groups()
            definitions[alias] = value.strip()
            continue
        for k, v in definitions.items():
            if isinstance(v, str):
                row = row.replace(k, v)
        res.append(row)
    return res


with open(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'rinterface_lib',
            'R_API.h')
        ) as fh:
    iterrows = iter(fh)
    cdef.extend(parse(iterrows, 0))

ffibuilder_abi.set_source('_rinterface_cffi_abi', None)
ffibuilder_abi.cdef(''.join(cdef))

r_home = rpy2.situation.r_home_from_subprocess()
c_ext = rpy2.situation.CExtensionOptions()
c_ext.add_lib(*rpy2.situation.get_r_flags(r_home, '--ldflags'))
c_ext.add_include(*rpy2.situation.get_r_flags(r_home, '--cppflags'))

ffibuilder_api.set_source('_rinterface_cffi_api',
                          ''.join(cdef),
                          libraries=c_ext.libraries,
                          library_dirs=c_ext.library_dirs,
                          include_dirs=c_ext.include_dirs)
cdef_api = (
    ''.join(cdef) +
    os.linesep.join(
        x.extern_python_def
        for x in [ffi_proxy._capsule_finalizer_def,
                  ffi_proxy._evaluate_in_r_def,
                  ffi_proxy._consoleflush_def,
                  ffi_proxy._consoleread_def,
                  ffi_proxy._consolereset_def,
                  ffi_proxy._consolewrite_def,
                  ffi_proxy._consolewrite_ex_def,
                  ffi_proxy._showmessage_def,
                  ffi_proxy._choosefile_def,
                  ffi_proxy._cleanup_def,
                  ffi_proxy._showfiles_def,
                  ffi_proxy._processevents_def,
                  ffi_proxy._busy_def,
                  ffi_proxy._callback_def,
                  ffi_proxy._yesnocancel_def])
    )
ffibuilder_api.cdef(cdef_api)

if __name__ == '__main__':
    ffibuilder_abi.compile(verbose=True)
    ffibuilder_api.compile(verbose=True)
