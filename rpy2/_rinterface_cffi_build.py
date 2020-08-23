import cffi
import os
import re
import sys
import warnings
import rpy2.situation
from rpy2.rinterface_lib import ffi_proxy

IFDEF_PAT = re.compile('^#ifdef (.+) ?.*$')
ELSE_PAT = re.compile('^#else ?.*$')
ENDIF_PAT = re.compile('^#endif ?.*$')
DEFINE_PAT = re.compile('^#define +([^ ]+) +([^ ]+) *$')


def _c_preprocess_block(csource,
                        definitions={}, rownum=0):
    localdefs = definitions.copy()
    block = []
    for row in csource:
        rownum += 1
        m = DEFINE_PAT.match(row)
        if m:
            localdefs[m.group(1)] = m.group(2)
            continue
        m_ifdef = IFDEF_PAT.match(row)
        if m_ifdef:
            subblock, subdefs = _c_preprocess_ifdef(
                csource,
                m_ifdef.group(1) in localdefs,
                definitions=localdefs,
                rownum=rownum)
            block.extend(subblock)
            definitions.update(subdefs)
            continue

        m_else = ELSE_PAT.match(row)
        if m_else:
            return ('else', block, definitions)

        m_endif = ENDIF_PAT.match(row)
        if m_endif:
            return ('endif', block, definitions)
        for k, v in localdefs.items():
            if isinstance(v, str):
                row = row.replace(k, v)
        block.append(row)


def _c_preprocess_ifdef(csource, want_block_a,
                        definitions={}, rownum=0):
    ending, block_a, defs_a = _c_preprocess_block(
        csource,
        definitions=definitions,
        rownum=rownum)
    if ending == 'else':
        ending, block_b, defs_b = _c_preprocess_block(
            csource,
            definitions=definitions,
            rownum=rownum)
    else:
        block_b = ''
        defs_b = definitions
    assert ending == 'endif'
    if want_block_a:
        return (block_a, defs_a)
    else:
        return (block_b, defs_b)


def c_preprocess(csource, definitions={}, rownum=0):
    """
    Rudimentary C-preprocessor for ifdef blocks.

    Args:
    - csource: iterator C source code
    - definitions: a mapping (e.g., set or dict contaning
      which "names" are defined)

    Returns:
    The csource with the conditional ifdef blocks for name
    processed.
    """

    localdefs = definitions.copy()
    block = []
    for row in csource:
        rownum += 1
        m = DEFINE_PAT.match(row)
        if m:
            localdefs[m.group(1)] = m.group(2)
            continue
        m_ifdef = IFDEF_PAT.match(row)
        if m_ifdef:
            name = m_ifdef.group(1)
            subblock, subdefs = _c_preprocess_ifdef(csource, name in localdefs,
                                                    definitions=localdefs,
                                                    rownum=0)
            block.extend(subblock)
            localdefs.update(subdefs)
            continue
        for k, v in localdefs.items():
            if isinstance(v, str):
                row = row.replace(k, v)
        block.append(row)
    return block, rownum


def define_rlen_kind(ffibuilder, definitions):
    if ffibuilder.sizeof('size_t') > 4:
        # The following was defined in the first cffi port,
        # and they in the C-extension version. They should
        # be ported to the header.
        # LONG_VECTOR_SUPPORT = True
        # R_XLEN_T_MAX = 4503599627370496
        # R_SHORT_LEN_MAX = 2147483647
        definitions['RPY2_RLEN_LONG'] = True


def define_osname(definitions):
    if os.name == 'nt':
        definitions['OSNAME_NT'] = True


def create_cdef(definitions, header_filename):
    cdef = []
    with open(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                'rinterface_lib',
                header_filename)
    ) as fh:
        cdef, _ = c_preprocess(fh, definitions=definitions, rownum=0)
    return ''.join(cdef)


def read_source(src_filename):
    with open(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                'rinterface_lib',
                src_filename)
    ) as fh:
        cdef = fh.read()
    return cdef


def createbuilder_abi():
    ffibuilder = cffi.FFI()
    definitions = {}
    define_rlen_kind(ffibuilder, definitions)
    define_osname(definitions)
    r_h = read_source('R_API.h')
    # TODO: is R_INTERFACE_PTRS defined for all non-Windows systems?
    if not os.name == 'nt':
        definitions['R_INTERFACE_PTRS'] = True
    cdef_r, _ = c_preprocess(
        iter(r_h.split('\n')),
        definitions=definitions,
        rownum=1)
    ffibuilder.set_source('_rinterface_cffi_abi', None)
    ffibuilder.cdef('\n'.join(cdef_r))
    return ffibuilder


def createbuilder_api():
    ffibuilder = cffi.FFI()
    definitions = {}
    define_rlen_kind(ffibuilder, definitions)
    define_osname(definitions)
    # TODO: is R_INTERFACE_PTRS defined for all non-Windows systems?
    if not os.name == 'nt':
        definitions['R_INTERFACE_PTRS'] = True

    r_h = read_source('R_API.h')
    eventloop_h = read_source('R_API_eventloop.h')
    eventloop_c = read_source('R_API_eventloop.c')
    rpy2_h = read_source('RPY2.h')
    r_home = rpy2.situation.get_r_home()
    if r_home is None:
        sys.exit('Error: rpy2 in API mode cannot be built without R in '
                 'the PATH or R_HOME defined. Correct this or force '
                 'ABI mode-only by defining the environment variable '
                 'RPY2_CFFI_MODE=ABI')
    c_ext = rpy2.situation.CExtensionOptions()
    c_ext.add_lib(
        *rpy2.situation.get_r_flags(r_home, '--ldflags')
    )
    c_ext.add_include(
        *rpy2.situation.get_r_flags(r_home, '--cppflags')
    )
    if 'RPY2_RLEN_LONG' in definitions:
        definitions['RPY2_RLEN_LONG'] = True

    ffibuilder.set_source(
        '_rinterface_cffi_api',
        eventloop_c + rpy2_h,
        libraries=c_ext.libraries,
        library_dirs=c_ext.library_dirs,
        # If we were using the R headers, we would use
        # include_dirs=c_ext.include_dirs.
        include_dirs=['rpy2/rinterface_lib/'],
        define_macros=list(definitions.items()),
        extra_compile_args=c_ext.extra_compile_args,
        extra_link_args=c_ext.extra_link_args)

    callback_defns_api = os.linesep.join(
        x.extern_python_def
        for x in [
                ffi_proxy._capsule_finalizer_def,
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
                ffi_proxy._yesnocancel_def,
                ffi_proxy._parsevector_wrap_def,
                ffi_proxy._handler_def,
                ffi_proxy._exec_findvar_in_frame_def
        ])

    cdef_r, _ = c_preprocess(
        iter(r_h.split('\n')),
        definitions=definitions,
        rownum=1)
    ffibuilder.cdef('\n'.join(cdef_r))

    ffibuilder.cdef(rpy2_h)
    ffibuilder.cdef(callback_defns_api)

    cdef_eventloop, _ = c_preprocess(
        iter(eventloop_h.split('\n')),
        definitions={'CFFI_SOURCE': True},
        rownum=1)
    ffibuilder.cdef('\n'.join(cdef_eventloop))
    ffibuilder.cdef('void rpy2_runHandlers(InputHandler *handlers);')
    return ffibuilder


# This sort of redundant with setup.py defining cffi_modules,
# but at least both use rpy2.situation.get_ffi_mode().
cffi_mode = rpy2.situation.get_cffi_mode()

if cffi_mode in (rpy2.situation.CFFI_MODE.ABI,
                 rpy2.situation.CFFI_MODE.BOTH):
    ffibuilder_abi = createbuilder_abi()
elif cffi_mode == rpy2.situation.CFFI_MODE.ANY:
    try:
        ffibuilder_abi = createbuilder_abi()
    except Exception as e:
        warnings.warn(str(e))
        ffibuilder_abi = None

if cffi_mode in (rpy2.situation.CFFI_MODE.API,
                 rpy2.situation.CFFI_MODE.BOTH):
    ffibuilder_api = createbuilder_api()
elif cffi_mode == rpy2.situation.CFFI_MODE.ANY:
    try:
        ffibuilder_api = createbuilder_api()
    except Exception as e:
        warnings.warn(str(e))
        ffibuilder_api = None

if __name__ == '__main__':

    if cffi_mode in (rpy2.situation.CFFI_MODE.ABI,
                     rpy2.situation.CFFI_MODE.BOTH):
        ffibuilder_abi.compile(verbose=True)
    elif cffi_mode == rpy2.situation.CFFI_MODE.ANY:
        try:
            ffibuilder_api.compile(verbose=True)
        except Exception as e:
            warnings.warn(str(e))

    if cffi_mode in (rpy2.situation.CFFI_MODE.API,
                     rpy2.situation.CFFI_MODE.BOTH):
        ffibuilder_api.compile(verbose=True)
    elif cffi_mode == rpy2.situation.CFFI_MODE.ANY:
        try:
            ffibuilder_api.compile(verbose=True)
        except Exception as e:
            warnings.warn(str(e))
