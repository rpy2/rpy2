"""Callbacks available from R's C-API.

The callbacks make available in R's C-API can be specified as
Python functions, with the module providing the adapter code
that makes it possible."""

from contextlib import contextmanager
import logging
import typing
from _rinterface_cffi import ffi
from . import conversion

logger = logging.getLogger(__name__)

READCONSOLE_SIGNATURE = 'int(char *, unsigned char *, int, int)'
RESETCONSOLE_SIGNATURE = 'void(void)'
WRITECONSOLE_SIGNATURE = 'void(char *, int)'
WRITECONSOLE_EX_SIGNATURE = 'void(char *, int, int)'
SHOWMESSAGE_SIGNATURE = 'void(char *)'
CHOOSEFILE_SIGNATURE = 'int(int, char *, int)'
CLEANUP_SIGNATURE = 'void(SA_TYPE, int, int)'
SHOWFILE_SIGNATURE = ('int(int, const char **, const char **, '
                      '    const char *, Rboolean, const char *)')


# TODO: rename to "replace_in_module"
@contextmanager
def obj_in_module(module, name: str, obj):
    obj_orig = getattr(module, name)
    setattr(module, name, obj)
    try:
        yield
    finally:
        setattr(module, name, obj_orig)


def consoleflush():
    pass


_FLUSHCONSOLE_EXCEPTION_LOG = 'R[flush console]: %s'


@ffi.callback('void (void)')
def _consoleflush():
    try:
        consoleflush()
    except Exception as e:
        logger.error(_FLUSHCONSOLE_EXCEPTION_LOG, str(e))


def consoleread(prompt: str) -> str:
    return input(prompt)


_READCONSOLE_EXCEPTION_LOG = 'R[read into console]: %s'
_READCONSOLE_INTERNAL_EXCEPTION_LOG = 'Internal rpy2 error with callback: %s'


@ffi.callback(READCONSOLE_SIGNATURE)
def _consoleread(prompt, buf, n: int, addtohistory) -> int:
    success = None
    try:
        s = conversion._cchar_to_str(prompt)
        reply = consoleread(s)
    except Exception as e:
        success = 0
        logger.error(_READCONSOLE_EXCEPTION_LOG, str(e))
    if success == 0:
        return success

    try:
        # TODO: handle non-ASCII encodings
        reply_b = reply.encode('ASCII')
        reply_n = min(n, len(reply_b))
        ffi.memmove(buf,
                    reply_b,
                    reply_n)
        if reply_n < n:
            buf[reply_n] = ord(b'\n')
        for i in range(reply_n+1, n):
            buf[i] = 0
        if reply_n == 0:
            success = 0
        else:
            success = 1
    except Exception as e:
        success = 0
        logger.error(_READCONSOLE_INTERNAL_EXCEPTION_LOG,
                     str(e))
    return success


def consolereset() -> None:
    pass


_RESETCONSOLE_EXCEPTION_LOG = 'R[reset console]: %s'


@ffi.callback(RESETCONSOLE_SIGNATURE)
def _consolereset() -> None:
    try:
        consolereset()
    except Exception as e:
        logger.error(_RESETCONSOLE_EXCEPTION_LOG, str(e))


def consolewrite_print(s: str) -> None:
    # TODO: is the callback for flush working with Linux ?
    print(s, end='', flush=True)


def consolewrite_warnerror(s: str) -> None:
    # TODO: use an rpy2/R-specific warning instead of UserWarning.
    logger.warning(_WRITECONSOLE_EXCEPTION_LOG, s)


_WRITECONSOLE_EXCEPTION_LOG = 'R[write to console]: %s'


@ffi.callback(WRITECONSOLE_EX_SIGNATURE)
def _consolewrite_ex(buf, n: int, otype) -> None:
    s = conversion._cchar_to_str_with_maxlen(buf, maxlen=n)
    try:
        if otype == 0:
            consolewrite_print(s)
        else:
            consolewrite_warnerror(s)
    except Exception as e:
        logger.error(_WRITECONSOLE_EXCEPTION_LOG, str(e))


def showmessage(s: str) -> None:
    print('R wants to show a message')
    print(s)


_SHOWMESSAGE_EXCEPTION_LOG = 'R[show message]: %s'


@ffi.callback(SHOWMESSAGE_SIGNATURE)
def _showmessage(buf):
    s = conversion._cchar_to_str(buf)
    try:
        showmessage(s)
    except Exception as e:
        logger.error(_SHOWMESSAGE_EXCEPTION_LOG, str(e))


def choosefile(new):
    return input('Enter file name:')


_CHOOSEFILE_EXCEPTION_LOG = 'R[choose file]: %s'


@ffi.callback(CHOOSEFILE_SIGNATURE)
def _choosefile(new, buf, n: int) -> int:
    try:
        res = choosefile(new)
    except Exception as e:
        logger.error(_CHOOSEFILE_EXCEPTION_LOG, str(e))
        res = None

    if res is None:
        return 0

    res_cdata = conversion._str_to_cchar(res)
    ffi.memmove(buf, res_cdata, len(res_cdata))
    return len(res_cdata)


def showfiles(filenames: typing.Tuple[str],
              headers: typing.Tuple[str],
              wtitle: str, pager: str) -> None:
    for fn in filenames:
        print('File: %s' % fn)
        with open(fn) as fh:
            for row in fh:
                print(row)
            print('---')


_SHOWFILE_EXCEPTION_LOG = 'R[show file]: %s'
_SHOWFILE_INTERNAL_EXCEPTION_LOG = ('Internal rpy2 error while '
                                    'showing files for R: %s')


@ffi.callback(SHOWFILE_SIGNATURE)
def _showfiles(nfiles: int, files, headers, wtitle, delete, pager) -> int:
    filenames = []
    headers_str = []
    wtitle_str = None
    pager_str = None
    try:
        wtitle_str = conversion._cchar_to_str(wtitle)
        pager_str = conversion._cchar_to_str(pager)
        for i in range(nfiles):
            filenames.append(conversion._cchar_to_str(files[i]))
            headers_str.append(conversion._cchar_to_str(headers[i]))
    except Exception as e:
        logger.error(_SHOWFILE_INTERNAL_EXCEPTION_LOG, str(e))

    if len(filenames):
        res = 0
    else:
        res = 1
    try:
        showfiles(tuple(filenames),
                  tuple(headers_str),
                  wtitle_str,
                  pager_str)
    except Exception as e:
        res = 1
        logger.error(_SHOWFILE_EXCEPTION_LOG, str(e))

    return res


def cleanup(saveact, status, runlast):
    pass


_CLEANUP_EXCEPTION_LOG = 'R[cleanup]: %s'


@ffi.callback(CLEANUP_SIGNATURE)
def _cleanup(saveact, status, runlast):
    try:
        cleanup(saveact, status, runlast)
    except Exception as e:
        logger.error(_CLEANUP_EXCEPTION_LOG, str(e))
