from contextlib import contextmanager
import logging
import typing
from . import _rinterface_capi as _rinterface

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


@contextmanager
def obj_in_module(module, name, func):
    backup_func = getattr(module, name)
    setattr(module, name, func)
    try:
        yield
    finally:
        setattr(module, name, backup_func)


# TODO: remove the decorator
def logged_exceptions(func, logger=logger):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(str(e))
    return wrapper


def consoleread(prompt: str) -> str:
    return input(prompt)


_READCONSOLE_EXCEPTION_LOG = 'Callback to read into the R console: %s'
_READCONSOLE_INTERNAL_EXCEPTION_LOG = 'Internal rpy2 error with callback: %s'


@_rinterface.ffi.callback(READCONSOLE_SIGNATURE)
def _consoleread(prompt, buf, n, addtohistory):
    success = None
    try:
        s = _rinterface._cchar_to_str(prompt)
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
        _rinterface.ffi.memmove(buf,
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
        logger.error(_READCONSOLE_INTERNAL_EXCEPTION_LOG, str(e))
    return success


@logged_exceptions
def consolereset() -> None:
    pass


_RESETCONSOLE_EXCEPTION_LOG = 'Callback to reset the R console: %s'


@_rinterface.ffi.callback(RESETCONSOLE_SIGNATURE)
def _consolereset():
    try:
        consolereset()
    except Exception as e:
        logger.error(_RESETCONSOLE_EXCEPTION_LOG, str(e))


@logged_exceptions
def consolewrite_print(s: str) -> None:
    # TODO: is the callback for flush working with Linux ?
    print(s, end='', flush=True)


@logged_exceptions
def consolewrite_warnerror(s: str) -> None:
    # TODO: use an rpy2/R-specific warning instead of UserWarning.
    logger.warning(_WRITECONSOLE_EXCEPTION_LOG, s)


_WRITECONSOLE_EXCEPTION_LOG = 'Callback to write to the R console: %s'


@_rinterface.ffi.callback(WRITECONSOLE_EX_SIGNATURE)
def _consolewrite_ex(buf, n, otype):
    s = _rinterface._cchar_to_str_with_maxlen(buf, maxlen=n)
    try:
        if otype == 0:
            consolewrite_print(s)
        else:
            consolewrite_warnerror(s)
    except Exception as e:
        logger.error(_WRITECONSOLE_EXCEPTION_LOG, str(e))


@logged_exceptions
def showmessage(s: str) -> None:
    print('R wants to show a message')
    print(s)


_SHOWMESSAGE_EXCEPTION_LOG = 'Callback to show R message: %s'


@_rinterface.ffi.callback(SHOWMESSAGE_SIGNATURE)
def _showmessage(buf):
    s = _rinterface._cchar_to_str(buf)
    try:
        showmessage(s)
    except Exception as e:
        logger.error(_SHOWMESSAGE_EXCEPTION_LOG, str(e))


@logged_exceptions
def choosefile(new):
    return input('Enter file name:')


_CHOOSEFILE_EXCEPTION_LOG = 'Callback to choose file from R: %s'


@_rinterface.ffi.callback(CHOOSEFILE_SIGNATURE)
def _choosefile(new, buf, n):
    try:
        res = choosefile(new)
    except Exception as e:
        logger.error(_CHOOSEFILE_EXCEPTION_LOG, str(e))
        res = None

    if res is None:
        return 0

    res_cdata = _rinterface._str_to_cchar(res)
    _rinterface.ffi.memmove(buf, res_cdata, len(res_cdata))
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



_SHOWFILE_EXCEPTION_LOG = 'Callback to shows file for R: %s'
_SHOWFILE_INTERNAL_EXCEPTION_LOG = 'Internal rpy2 error while showing files for R: %s'


@_rinterface.ffi.callback(SHOWFILE_SIGNATURE)
def _showfiles(nfiles, files, headers, wtitle, delete, pager):
    filenames = []
    headers_str = []
    wtitle_str = None
    pager_str = None
    try:
        wtitle_str = _rinterface._cchar_to_str(wtitle)
        pager_str = _rinterface._cchar_to_str(pager)
        for i in range(nfiles):
            filenames.append(_rinterface._cchar_to_str(files[i]))
            headers_str.append(_rinterface._cchar_to_str(headers[i]))
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

            
@logged_exceptions
def cleanup(saveact, status, runlast):
    pass


_CLEANUP_EXCEPTION_LOG = 'Callback to clean up R: %s'


@_rinterface.ffi.callback(CLEANUP_SIGNATURE)
def _cleanup(saveact, status, runlast):
    try:
        cleanup(saveact, status, runlast)
    except Exception as e:
        logger.error(_CLEANUP_EXCEPTION_LOG, str(e))
